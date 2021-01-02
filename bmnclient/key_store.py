from enum import Enum
import json
import os
from json.decoder import JSONDecodeError
from threading import Lock
from typing import Optional

from PySide2.QtCore import Slot as QSlot, Signal as QSignal, \
    Property as QProperty, QObject

from . import version
from .config import UserConfig
from .crypto.cipher import Cipher
from .crypto.password import PasswordStrength
from .crypto.kdf import SecretStore
from .logger import getClassLogger
from .ui.gui import import_export
from .wallet import hd, mnemonic, util

MNEMONIC_SEED_LENGTH = 24
PASSWORD_HASHER = util.sha256


class KeyIndex(Enum):
    WALLET_DATABASE = 0


class KeyStore(QObject):
    """
    Holding hierarchy according to bip0044
    """
    mnemoRequested = QSignal()

    def __init__(self, user_config: UserConfig):
        super().__init__()
        self._user_config = user_config
        self._logger = getClassLogger(__name__, self.__class__)
        self._lock = Lock()

        self._nonce_list = [None] * len(KeyIndex)
        self._key_list = [None] * len(KeyIndex)

        # TODO
        self.__master_hd = None
        self.__mnemonic = mnemonic.Mnemonic()
        # don't keep mnemo, save seed instead !!!
        self.__seed = None
        # mb we can use one seed variable?
        self.__pre_hash = None

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

    @QSlot(str, result=bool)
    def preparePhrase(self, mnemonic_phrase: str) -> bool:
        mnemonic_phrase = " ".join(mnemonic_phrase.split())
        self._logger.debug(f"pre phrase: {mnemonic_phrase}")
        self.__pre_hash = util.sha256(mnemonic_phrase)
        return True

    @QSlot(str, bool, result=bool)
    def generateMasterKey(self, mnemonic_phrase: str, debug: bool = False) -> bool:
        mnemonic_phrase = " ".join(mnemonic_phrase.split())
        hash_ = util.sha256(mnemonic_phrase)
        if self.__pre_hash is None or hash_ == self.__pre_hash:
            seed = mnemonic.Mnemonic.to_seed(
                mnemonic_phrase,
            )
            self.apply_master_seed(
                seed,
                save=True,
            )
            self.gcd.save_mnemo(mnemonic_phrase)
            return True
        self._logger.warning(
            f"seed '{mnemonic_phrase}' mismatch: {hash_} != {self.__pre_hash}")
        return False

    @QSlot(float, result=str)
    def getInitialPassphrase(self, extra__seed: float = None) -> str:
        data = os.urandom(MNEMONIC_SEED_LENGTH)
        if extra__seed:
            # a little bit silly but let it be
            data = util.sha256(data + str(extra__seed).encode()
                               )[:MNEMONIC_SEED_LENGTH]
        else:
            self._logger.warning("No extra!!!")
        return self.__mnemonic.get_phrase(data)

    def regenerate_master_key(self):
        seed = mnemonic.Mnemonic.to_seed(
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
            self.gcd.save_master_seed(self.master_seed_hex)

    @QSlot(str, result=bool)
    def validateSeed(self, seed: str) -> bool:
        try:
            self.__mnemonic.check_words(seed)
            return True
        except ValueError as ve:
            self._logger.warning(f"seed validation error: {ve} => {seed}")
            return False

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

    @QSlot()
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
