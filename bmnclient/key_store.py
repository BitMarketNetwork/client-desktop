from enum import Enum
import json
import os
from json.decoder import JSONDecodeError
from threading import RLock
from typing import Optional

from PySide2.QtCore import Slot as QSlot, Signal as QSignal, \
    Property as QProperty, QObject

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.hashes import Hash

from . import version
from .config import UserConfig
from .crypto.cipher import Cipher
from .crypto.password import PasswordStrength
from .crypto.kdf import SecretStore
from .logger import getClassLogger
from .ui.gui import import_export
from .wallet import hd, mnemonic, util
from .wallet.mnemonic import Mnemonic

MNEMONIC_SEED_LENGTH = 24


class KeyIndex(Enum):
    WALLET_DATABASE = 0


class KeyStore(QObject):
    mnemoRequested = QSignal()

    def __init__(self, user_config: UserConfig):
        super().__init__()
        self._user_config = user_config
        self._logger = getClassLogger(__name__, self.__class__)
        self._lock = RLock()

        self._nonce_list = [None] * len(KeyIndex)
        self._key_list = [None] * len(KeyIndex)

        self._mnemonic = None
        self._mnemonic_salt_hash = None

        # TODO
        self.__master_hd = None
        self.__seed = None

    def _getNonce(self, key_index: KeyIndex) -> Optional[bytes]:
        return self._nonce_list[key_index.value]

    def _getKey(self, key_index: KeyIndex) -> Optional[bytes]:
        return self._key_list[key_index.value]

    def deriveCipher(self, key_index: KeyIndex) -> Optional[Cipher]:
        with self._lock:
            return Cipher(self._getKey(key_index), self._getNonce(key_index))

    @classmethod
    def _generateSecretStoreValue(cls) -> bytes:
        value = {
            "version":
                version.VERSION_STRING,
            "nonce_{:d}".format(KeyIndex.WALLET_DATABASE.value):
                Cipher.generateNonce().hex(),
            "key_{:d}".format(KeyIndex.WALLET_DATABASE.value):
                Cipher.generateKey().hex()
        }
        return json.dumps(value).encode(encoding=version.ENCODING)

    def _loadSecretStoreValue(self, value: bytes) -> bool:
        try:
            value = json.loads(value.decode(encoding=version.ENCODING))
            for k, v in value.items():
                if k.startswith("nonce_"):
                    k = int(k[6:])
                    self._nonce_list[k] = bytes.fromhex(v)
                elif k.startswith("key_"):
                    k = int(k[4:])
                    self._key_list[k] = bytes.fromhex(v)
        except (IndexError, ValueError, TypeError, JSONDecodeError):
            return False
        return True

    def _resetSecretStoreValue(self) -> None:
        self._nonce_list = [None] * len(self._nonce_list)
        self._key_list = [None] * len(self._key_list)

    ############################################################################
    # TODO

    def regenerate_master_key(self):
        seed = mnemonic.Mnemonic.toSeed(
            self.gcd.get_mnemo(),
        )
        self.apply_master_seed(
            seed,
            save=True,
        )

    @QSlot(str, result=str)
    def revealSeedPhrase(self, password: str):
        return self.gcd.get_mnemo(password) or self.tr("Wrong password")

    @QSlot()
    def resetWallet(self):
        self.gcd.reset_wallet()
        self.mnemoRequested.emit()

    @QSlot()
    def exportWallet(self):
        iexport = import_export.ImportExportDialog()
        filename = iexport.doExport(
            self.tr("Select file to save backup copy"))
        if filename:
            self.gcd.export_wallet(filename)

    @QSlot(result=bool)
    def importWallet(self) -> bool:
        iexport = import_export.ImportExportDialog()
        filename = iexport.doImport(
            self.tr("Select file with backup"))
        self._logger.debug(f"Import result: {filename}")
        if filename:
            self.gcd.import_wallet(filename)
            return True
        return False

    def apply_master_seed(self, seed: bytes, *, save: bool):
        """
        applies master seed
        """
        self.__seed = seed
        self.__master_hd = hd.HDNode.make_master(self.__seed)
        _44_node = self.__master_hd.make_child_prv(44, True)
        # iterate all 'cause we need test coins
        for coin in self.gcd.all_coins:
            if coin.enabled:
                coin.make_hd_node(_44_node)
                self._logger.debug(f"Make HD prv for {coin}")
        if save:
            self.saveMeta.emit("seed", self.master_seed_hex)

    @property
    def gcd(self):
        from .application import CoreApplication
        return CoreApplication.instance().gcd

    @property
    def master_key(self):
        return self.__master_hd

    @property
    def master_seed_hex(self) -> str:
        return util.bytes_to_hex(self.__seed)

    ############################################################################

    @QSlot(str, result=str)
    def prepareGenerateSeedPhrase(self, language: str = None) -> str:
        with self._lock:
            self._mnemonic = Mnemonic(language)
            self._mnemonic_salt_hash = Hash(hashes.SHA256())
            self._mnemonic_salt_hash.update(os.urandom(64))
            result = self._mnemonic_salt_hash.copy().finalize()
            result = result[:MNEMONIC_SEED_LENGTH]
            return self._mnemonic.getPhrase(result)

    @QSlot(str, result=str)
    def updateGenerateSeedPhrase(self, salt: Optional[str]) -> str:
        with self._lock:
            if self._mnemonic and self._mnemonic_salt_hash:
                if salt:
                    self._mnemonic_salt_hash.update(
                        salt.encode(encoding=version.ENCODING))
                    self._mnemonic_salt_hash.update(os.urandom(4))
                result = self._mnemonic_salt_hash.copy().finalize()
                result = result[:MNEMONIC_SEED_LENGTH]
                return self._mnemonic.getPhrase(result)
        return ""

    @QSlot(str, result=bool)
    def validateGenerateSeedPhrase(self, phrase: str) -> bool:
        if len(phrase) <= 0:
            return False
        phrase = Mnemonic.normalizePhrase(phrase)
        return phrase == self.updateGenerateSeedPhrase(None)

    @QSlot(str, result=bool)
    def finalizeGenerateSeedPhrase(self, phrase: str) -> bool:
        if len(phrase) <= 0:
            return False
        phrase = Mnemonic.normalizePhrase(phrase)
        with self._lock:
            if phrase != self.updateGenerateSeedPhrase(None):
                return False
            self._mnemonic = None
            self._mnemonic_salt_hash = None
            seed = Mnemonic.phraseToSeed(phrase)
            # TODO save
            self.apply_master_seed(seed, save=True)
            return True

    @QSlot(str, result=bool)
    def isValidSeedPhrase(self, phrase: str) -> bool:
        return self._mnemonic and self._mnemonic.isValidPhrase(phrase)

    @QSlot(str, result=int)
    def calcPasswordStrength(self, password: str) -> int:
        return PasswordStrength(password).calc()

    @QSlot(str, result=bool)
    def createPassword(self, password: str) -> bool:
        value = SecretStore(password).createValue(
            self._generateSecretStoreValue())
        with self._lock:
            return self._user_config.set(
                UserConfig.KEY_KEY_STORE_VALUE,
                value)

    @QSlot(str, result=bool)
    def setPassword(self, password: str) -> bool:
        with self._lock:
            value = self._user_config.get(
                UserConfig.KEY_KEY_STORE_VALUE,
                str)
            if not value:
                return False
            value = SecretStore(password).verifyValue(value)
            if not value or not self._loadSecretStoreValue(value):
                return False

        from .application import CoreApplication
        if CoreApplication.instance():
            CoreApplication.instance().gcd.apply_password()  # TODO
        return True

    @QSlot(result=bool)
    def resetPassword(self) -> bool:
        with self._lock:
            if not self._user_config.set(
                    UserConfig.KEY_KEY_STORE_VALUE,
                    None):
                return False
            self._resetSecretStoreValue()

        from .application import CoreApplication
        if CoreApplication.instance():
            CoreApplication.instance().gcd.reset_db()  # TODO
        return True

    @QProperty(bool, constant=True)
    def hasPassword(self) -> bool:
        with self._lock:
            value = self._user_config.get(
                UserConfig.KEY_KEY_STORE_VALUE,
                str)
        return value and len(value) > 0
