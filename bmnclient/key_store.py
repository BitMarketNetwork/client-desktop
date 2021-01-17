import json
import os
from enum import Enum
from json.decoder import JSONDecodeError
from threading import RLock
from typing import Optional, Tuple

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.hashes import Hash

from . import version
from .config import UserConfig
from .crypto.cipher import Cipher, MessageCipher
from .crypto.kdf import SecretStore
from .crypto.password import PasswordStrength
from .logger import getClassLogger
from .ui.gui import import_export
from .wallet import hd
from .wallet.mnemonic import Mnemonic


class KeyIndex(Enum):
    WALLET_DATABASE = 0
    SEED = 1


class KeyStore(QObject):
    mnemoRequested = QSignal()

    def __init__(self, user_config: UserConfig) -> None:
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

    def _reset(self) -> None:
        with self._lock:
            self._nonce_list = [None] * len(self._nonce_list)
            self._key_list = [None] * len(self._key_list)
            self._mnemonic = None
            self._mnemonic_salt_hash = None

            with self._user_config.lock:
                for key in (
                        UserConfig.KEY_KEY_STORE_VALUE,
                        UserConfig.KEY_KEY_STORE_SEED,
                        UserConfig.KEY_KEY_STORE_SEED_PHRASE):
                    self._user_config.set(key, None, save=False)
                self._user_config.save()

    def _getNonce(self, key_index: KeyIndex) -> Optional[bytes]:
        return self._nonce_list[key_index.value]

    def _getKey(self, key_index: KeyIndex) -> Optional[bytes]:
        return self._key_list[key_index.value]

    def deriveCipher(self, key_index: KeyIndex) -> Optional[Cipher]:
        with self._lock:
            assert self._getKey(key_index)
            assert self._getNonce(key_index)
            return Cipher(self._getKey(key_index), self._getNonce(key_index))

    def deriveMessageCipher(self, key_index: KeyIndex) -> Optional[Cipher]:
        with self._lock:
            assert self._getKey(key_index)
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

    ############################################################################
    # TODO

    def regenerate_master_key(self):
        seed = mnemonic.Mnemonic.phraseToSeed(self.gcd.get_mnemo())
        self.apply_master_seed(seed, save=True)

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
        from .application import CoreApplication
        if not CoreApplication.instance():
            return

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
            if self.validateGenerateSeedPhrase(phrase):
                if self._saveSeedWithPhrase(self._mnemonic.language, phrase):
                    self._mnemonic = None
                    self._mnemonic_salt_hash = None
                    return True
        return False

    @QSlot(str, result=bool)
    def prepareRestoreSeedPhrase(self, language: str = None) -> bool:
        with self._lock:
            self._mnemonic = Mnemonic(language)
            self._mnemonic_salt_hash = None
        return True

    @QSlot(str, result=bool)
    def validateRestoreSeedPhrase(self, phrase: str) -> bool:
        with self._lock:
            if self._mnemonic and self._mnemonic.isValidPhrase(phrase):
                return True
        return False

    @QSlot(str, result=bool)
    def finalizeRestoreSeedPhrase(self, phrase: str) -> bool:
        with self._lock:
            if self._mnemonic and self._mnemonic.isValidPhrase(phrase):
                if self._saveSeedWithPhrase(self._mnemonic.language, phrase):
                    self._mnemonic = None
                    self._mnemonic_salt_hash = None
                    return True
        return False

    @QSlot(str, result=str)
    def revealSeedPhrase(self, password: str):
        with self._lock:
            if not self.verifyPassword(password):
                return self.tr("Wrong password.")
            phrase = self._getSeedPhrase()
            if not phrase:
                return self.tr("Seed phrase not found.")
            return phrase[1]

    def _saveSeedWithPhrase(self, language: str, phrase: str) -> bool:
        if version.STRING_SEPARATOR in language:
            return False

        seed = Mnemonic.phraseToSeed(phrase)
        phrase = version.STRING_SEPARATOR.join((language, phrase))

        with self._user_config.lock:
            if not self._user_config.set(
                    UserConfig.KEY_KEY_STORE_SEED,
                    self.deriveMessageCipher(KeyIndex.SEED).encrypt(seed),
                    save=False):
                return False
            if not self._user_config.set(
                    UserConfig.KEY_KEY_STORE_SEED_PHRASE,
                    self.deriveMessageCipher(KeyIndex.SEED).encrypt(
                        phrase.encode(encoding=version.ENCODING)),
                    save=False):
                return False
            if not self._user_config.save():
                return False
        self.apply_master_seed(seed, save=True)
        return True

    def _getSeed(self) -> Optional[bytes]:
        value = self._user_config.get(UserConfig.KEY_KEY_STORE_SEED, str)
        if not value:
            return None
        return self.deriveMessageCipher(KeyIndex.SEED).decrypt(value)

    def _getSeedPhrase(self) -> Optional[Tuple[str, str]]:
        value = self._user_config.get(UserConfig.KEY_KEY_STORE_SEED_PHRASE, str)
        if not value:
            return None
        value = self.deriveMessageCipher(KeyIndex.SEED).decrypt(value)
        try:
            value = value.decode(encoding=version.ENCODING)
            (language, phrase) = value.split(version.STRING_SEPARATOR, 1)
        except (UnicodeError, ValueError):
            return None

        language = language.lower()
        phrase = Mnemonic.friendlyPhrase(language, phrase)
        return language, phrase

    ############################################################################

    @QSlot(str, result=int)
    def calcPasswordStrength(self, password: str) -> int:
        return PasswordStrength(password).calc()

    @QSlot(str, result=bool)
    def createPassword(self, password: str) -> bool:
        value = self._generateSecretStoreValue()
        value = SecretStore(password).encryptValue(value)
        with self._lock:
            self._reset()
            return self._user_config.set(UserConfig.KEY_KEY_STORE_VALUE, value)

    @QSlot(str, result=bool)
    def applyPassword(self, password: str) -> bool:
        with self._lock:
            value = self._user_config.get(UserConfig.KEY_KEY_STORE_VALUE, str)
            if not value:
                return False
            value = SecretStore(password).decryptValue(value)
            if not value or not self._loadSecretStoreValue(value):
                return False

        from .application import CoreApplication
        if CoreApplication.instance():
            CoreApplication.instance().gcd.apply_password()  # TODO
        return True

    @QSlot(str, result=bool)
    def verifyPassword(self, password: str) -> bool:
        with self._lock:
            value = self._user_config.get(UserConfig.KEY_KEY_STORE_VALUE, str)
            if value and SecretStore(password).decryptValue(value):
                return True
        return False

    @QSlot(result=bool)
    def resetPassword(self) -> bool:
        self._reset()
        from .application import CoreApplication
        if CoreApplication.instance():
            CoreApplication.instance().gcd.reset_db()  # TODO
        return True

    @QProperty(bool, constant=True)
    def hasPassword(self) -> bool:
        with self._lock:
            value = self._user_config.get(UserConfig.KEY_KEY_STORE_VALUE, str)
        if value and len(value) > 0:
            return True
        return False
