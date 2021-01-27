import json
import os
from enum import Enum
from json.decoder import JSONDecodeError
from threading import RLock
from typing import Optional, Tuple, List

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Slot as QSlot
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.hashes import Hash

from .config import UserConfig
from .crypto.cipher import AeadCipher, MessageCipher
from .crypto.kdf import SecretStore
from .crypto.password import PasswordStrength
from .logger import Logger
from .version import Product
from .wallet import hd
from .wallet.mnemonic import Mnemonic


class KeyIndex(Enum):
    WALLET_DATABASE = 0
    SEED = 1


class KeyStore(QObject):
    def __init__(self, user_config: UserConfig) -> None:
        super().__init__()
        self._user_config = user_config
        self._logger = Logger.getClassLogger(__name__, self.__class__)
        self._lock = RLock()

        self._nonce_list: List[Optional[bytes]] = [None] * len(KeyIndex)
        self._key_list: List[Optional[bytes]] = [None] * len(KeyIndex)

        self._mnemonic: Optional[Mnemonic] = None
        self._mnemonic_salt_hash: Optional[Hash] = None

        self._has_seed = False

    def _reset(self, *, hard: bool = True) -> None:
        self._nonce_list = [None] * len(self._nonce_list)
        self._key_list = [None] * len(self._key_list)
        self._mnemonic = None
        self._mnemonic_salt_hash = None
        self._has_seed = False

        if hard:
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

    def deriveCipher(self, key_index: KeyIndex) -> Optional[AeadCipher]:
        with self._lock:
            assert self._getKey(key_index)
            assert self._getNonce(key_index)
            return AeadCipher(
                self._getKey(key_index),
                self._getNonce(key_index))

    def deriveMessageCipher(self, key_index: KeyIndex) -> Optional[AeadCipher]:
        with self._lock:
            assert self._getKey(key_index)
            return MessageCipher(self._getKey(key_index))

    @classmethod
    def _generateSecretStoreValue(cls) -> bytes:
        value = {
            "version":
                Product.VERSION_STRING,

            "nonce_{:d}".format(KeyIndex.WALLET_DATABASE.value):
                AeadCipher.generateNonce().hex(),
            "key_{:d}".format(KeyIndex.WALLET_DATABASE.value):
                AeadCipher.generateKey().hex(),

            "nonce_{:d}".format(KeyIndex.SEED.value):
                MessageCipher.generateNonce().hex(),
            "key_{:d}".format(KeyIndex.SEED.value):
                MessageCipher.generateKey().hex()
        }
        return json.dumps(value).encode(encoding=Product.ENCODING)

    def _loadSecretStoreValue(self, value: bytes) -> bool:
        try:
            value = json.loads(value.decode(encoding=Product.ENCODING))
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
                        salt.encode(encoding=Product.ENCODING))
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
                    return self._loadSeed()
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
                    return self._loadSeed()
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

    @QProperty(bool, constant=True)
    def hasSeed(self) -> bool:
        with self._lock:
            return self._has_seed

    def _saveSeedWithPhrase(self, language: str, phrase: str) -> bool:
        if Product.STRING_SEPARATOR in language:
            return False

        seed = Mnemonic.phraseToSeed(phrase)
        phrase = Product.STRING_SEPARATOR.join((language, phrase))

        with self._user_config.lock:
            if not self._user_config.set(
                    UserConfig.KEY_KEY_STORE_SEED,
                    self.deriveMessageCipher(KeyIndex.SEED).encrypt(seed),
                    save=False):
                return False
            if not self._user_config.set(
                    UserConfig.KEY_KEY_STORE_SEED_PHRASE,
                    self.deriveMessageCipher(KeyIndex.SEED).encrypt(
                        phrase.encode(encoding=Product.ENCODING)),
                    save=False):
                return False
            if not self._user_config.save():
                return False
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
            value = value.decode(encoding=Product.ENCODING)
            (language, phrase) = value.split(Product.STRING_SEPARATOR, 1)
        except (UnicodeError, ValueError):
            return None

        language = language.lower()
        phrase = Mnemonic.friendlyPhrase(language, phrase)
        return language, phrase

    def _loadSeed(self) -> bool:
        seed = self._getSeed()
        if not seed:
            return False

        # TODO
        master_hd = hd.HDNode.make_master(seed)
        _44_node = master_hd.make_child_prv(44, True)
        from .application import CoreApplication
        if CoreApplication.instance():
            for coin in CoreApplication.instance().coinList:
                if coin.enabled:
                    coin.make_hd_node(_44_node)
                    self._logger.debug(f"Make HD prv for {coin}")
            from .ui.gui import Application
            Application.instance().networkThread.look_for_HD()
        return True

    ############################################################################

    @QSlot(str, result=int)
    def calcPasswordStrength(self, password: str) -> int:
        return PasswordStrength(password).calc()

    @QSlot(str, result=bool)
    def createPassword(self, password: str) -> bool:
        value = self._generateSecretStoreValue()
        value = SecretStore(password).encryptValue(value)
        with self._lock:
            self._reset(hard=True)
            return self._user_config.set(UserConfig.KEY_KEY_STORE_VALUE, value)

    @QSlot(str, result=bool)
    def applyPassword(self, password: str) -> bool:
        with self._lock:
            self._reset(hard=False)
            value = self._user_config.get(UserConfig.KEY_KEY_STORE_VALUE, str)
            if not value:
                return False
            value = SecretStore(password).decryptValue(value)
            if not value or not self._loadSecretStoreValue(value):
                return False
            self._has_seed = self._loadSeed()

        from .application import CoreApplication
        if CoreApplication.instance():
            CoreApplication.instance().databaseThread.applyPassword.emit()
            CoreApplication.instance().networkThread.startTimers()
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
        with self._lock:
            self._reset(hard=True)

        from .application import CoreApplication
        if CoreApplication.instance():
            CoreApplication.instance().databaseThread.reset_db()  # TODO
        return True

    @QProperty(bool, constant=True)
    def hasPassword(self) -> bool:
        with self._lock:
            if self._user_config.get(UserConfig.KEY_KEY_STORE_VALUE, str):
                return True
        return False
