import json
import os
from enum import Enum
from json.decoder import JSONDecodeError
from threading import RLock
from typing import Optional, Tuple

from PySide2.QtCore import Slot as QSlot, Signal as QSignal, \
    Property as QProperty, QObject
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.hashes import Hash

from . import version
from .config import UserConfig
from .crypto.cipher import Cipher, MessageCipher
from .crypto.kdf import SecretStore
from .crypto.password import PasswordStrength
from .logger import getClassLogger
from .ui.gui import import_export
from .wallet import hd, mnemonic
from .wallet.mnemonic import Mnemonic


class KeyIndex(Enum):
    WALLET_DATABASE = 0
    SEED = 1


class KeyStore(QObject):
    mnemoRequested = QSignal()

    def __init__(self, user_config: UserConfig):
        super().__init__()
        self._user_config = user_config
        self._logger = getClassLogger(__name__, self.__class__)
        self._lock = RLock()

        self._nonce_list = [None] * len(KeyIndex)
        self._key_list = [None] * len(KeyIndex)

        self._mnemonic: Optional[Mnemonic] = None
        self._mnemonic_salt_hash: Optional[Hash] = None

        # TODO
        self.__master_hd = None

    def _getNonce(self, key_index: KeyIndex) -> Optional[bytes]:
        return self._nonce_list[key_index.value]

    def _getKey(self, key_index: KeyIndex) -> Optional[bytes]:
        return self._key_list[key_index.value]

    def deriveCipher(self, key_index: KeyIndex) -> Optional[Cipher]:
        with self._lock:
            return Cipher(self._getKey(key_index), self._getNonce(key_index))

    def deriveMessageCipher(self, key_index: KeyIndex) -> Optional[Cipher]:
        with self._lock:
            return MessageCipher(self._getKey(key_index))

    @classmethod
    def _generateSecretStoreValue(cls) -> bytes:
        value = {
            "version":
                version.VERSION_STRING,

            "nonce_{:d}".format(KeyIndex.WALLET_DATABASE.value):
                Cipher.generateNonce().hex(),
            "key_{:d}".format(KeyIndex.WALLET_DATABASE.value):
                Cipher.generateKey().hex(),

            "nonce_{:d}".format(KeyIndex.SEED.value):
                MessageCipher.generateNonce().hex(),
            "key_{:d}".format(KeyIndex.SEED.value):
                MessageCipher.generateKey().hex()
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
        seed = mnemonic.Mnemonic.phraseToSeed(self.gcd.get_mnemo())
        self.apply_master_seed(seed, save=True)

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
        self.__master_hd = hd.HDNode.make_master(seed)
        _44_node = self.__master_hd.make_child_prv(44, True)
        # iterate all 'cause we need test coins
        for coin in self.gcd.all_coins:
            if coin.enabled:
                coin.make_hd_node(_44_node)
                self._logger.debug(f"Make HD prv for {coin}")
        if save:
            self.gcd.saveMeta.emit("seed", seed.hex())

    @property
    def gcd(self):
        from .application import CoreApplication
        return CoreApplication.instance().gcd

    @property
    def master_key(self):
        return self.__master_hd

    ############################################################################

    @QSlot(str, result=str)
    def prepareGenerateSeedPhrase(self, language: str = None) -> str:
        with self._lock:
            self._mnemonic = Mnemonic(language)
            self._mnemonic_salt_hash = Hash(hashes.SHA256())
            self._mnemonic_salt_hash.update(os.urandom(64))
            result = self._mnemonic_salt_hash.copy().finalize()
            result = result[:Mnemonic.DEFAULT_DATA_LENGTH]
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
                result = result[:Mnemonic.DEFAULT_DATA_LENGTH]
                return self._mnemonic.getPhrase(result)
        return ""

    @QSlot(str, result=bool)
    def validateGenerateSeedPhrase(self, phrase: str) -> bool:
        return Mnemonic.isEqualPhrases(
            phrase,
            self.updateGenerateSeedPhrase(None))

    @QSlot(str, result=bool)
    def finalizeGenerateSeedPhrase(self, phrase: str) -> bool:
        with self._lock:
            if not self.validateGenerateSeedPhrase(phrase):
                return False
            return self._saveSeedFromPhrase(phrase)

    @QSlot(str, result=bool)
    def prepareRestoreSeedPhrase(self, language: str = None) -> bool:
        with self._lock:
            self._mnemonic = Mnemonic(language)
            self._mnemonic_salt_hash = None
        return True

    @QSlot(str, result=bool)
    def validateRestoreSeedPhrase(self, phrase: str) -> bool:
        with self._lock:
            return self._mnemonic and self._mnemonic.isValidPhrase(phrase)

    @QSlot(str, result=bool)
    def finalizeRestoreSeedPhrase(self, phrase: str) -> bool:
        with self._lock:
            if not self._mnemonic or not self._mnemonic.isValidPhrase(phrase):
                return False
            return self._saveSeedFromPhrase(phrase)

    def _saveSeedFromPhrase(self, phrase: str) -> bool:
        assert self._mnemonic
        seed = Mnemonic.phraseToSeed(phrase)
        value = version.STRING_SEPARATOR.join((
            self._mnemonic.language,
            seed.hex())).encode(encoding=version.ENCODING)
        value = self.deriveMessageCipher(KeyIndex.SEED).encrypt(value)
        if not self._user_config.set(
                UserConfig.KEY_KEY_STORE_SEED,
                value):
            return False

        self._mnemonic = None
        self._mnemonic_salt_hash = None

        from .application import CoreApplication
        if CoreApplication.instance():
            self.apply_master_seed(seed, save=True)
        return True

    def _loadSeed(self) -> Optional[Tuple[str, bytes]]:
        value = self._user_config.get(UserConfig.KEY_KEY_STORE_SEED, str)
        if not value:
            return None
        value = self.deriveMessageCipher(KeyIndex.SEED).decrypt(value)
        if not value:
            return None
        try:
            value = value.decode(encoding=version.ENCODING)
            (language, seed) = value.split(version.STRING_SEPARATOR, 1)
            seed = bytes.fromhex(seed)
        except (UnicodeError, ValueError):
            return None
        return language, seed

    ############################################################################

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
    def applyPassword(self, password: str) -> bool:
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
