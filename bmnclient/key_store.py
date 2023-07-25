from __future__ import annotations

import json
import os
from enum import Enum
from json.decoder import JSONDecodeError
from threading import RLock
from typing import TYPE_CHECKING

from .coins.hd import HdNode
from .coins.mnemonic import Mnemonic
from .config import KeyStoreConfig
from .crypto.cipher import AeadCipher, MessageCipher
from .crypto.digest import Sha256Digest
from .crypto.kdf import SecretStore
from .logger import Logger
from .version import Product

if TYPE_CHECKING:
    from typing import Callable, Final, Union

    from .application import CoreApplication
    from .crypto.digest import AbstractDigest


class KeyIndex(Enum):
    WALLET_DATABASE: Final = 0
    SEED: Final = 1


class KeyStoreError(Enum):
    SUCCESS: Final = 0
    ERROR_UNKNOWN: Final = 1
    ERROR_INVALID_PASSWORD: Final = 1000
    ERROR_SEED_NOT_FOUND: Final = 2000
    ERROR_SAVE_SEED: Final = 2001
    ERROR_INVALID_SEED_PHRASE: Final = 2002
    ERROR_DERIVE_ROOT_HD_NODE: Final = 3000


class _KeyStoreBase:
    def __init__(self, application: CoreApplication) -> None:
        self._logger = Logger.classLogger(self.__class__)
        self._lock = RLock()
        self._application = application
        self._config: None | KeyStoreConfig = None

        self.__nonce_list: list[bytes | None] = [None] * len(KeyIndex)
        self.__key_list: list[bytes | None] = [None] * len(KeyIndex)

    @property
    def config(self) -> KeyStoreConfig | None:
        return self._config

    @config.setter
    def config(self, value: KeyStoreConfig | None) -> None:
        self._config = value

    def __clearSecrets(self) -> None:
        self.__nonce_list = [None] * len(KeyIndex)
        self.__key_list = [None] * len(KeyIndex)

    def _clear(self) -> None:
        self.__clearSecrets()

    def _getNonce(self, key_index: KeyIndex) -> bytes | None:
        return self.__nonce_list[key_index.value]

    def _getKey(self, key_index: KeyIndex) -> bytes | None:
        return self.__key_list[key_index.value]

    @staticmethod
    def _generateSecretStoreValue() -> bytes:
        value = {
            "version": Product.VERSION_STRING,
            "nonce_{:d}".format(
                KeyIndex.WALLET_DATABASE.value
            ): AeadCipher.generateNonce().hex(),
            "key_{:d}".format(
                KeyIndex.WALLET_DATABASE.value
            ): AeadCipher.generateKey().hex(),
            "nonce_{:d}".format(
                KeyIndex.SEED.value
            ): MessageCipher.generateNonce().hex(),
            "key_{:d}".format(
                KeyIndex.SEED.value
            ): MessageCipher.generateKey().hex(),
        }
        return json.dumps(value).encode(Product.ENCODING)

    def _loadSecretStoreValue(self, value: bytes) -> bool:
        self.__clearSecrets()
        try:
            value = json.loads(value.decode(Product.ENCODING))
            for k, v in value.items():
                if k.startswith("nonce_"):
                    k = int(k[6:])
                    self.__nonce_list[k] = bytes.fromhex(v)
                elif k.startswith("key_"):
                    k = int(k[4:])
                    self.__key_list[k] = bytes.fromhex(v)
        except (IndexError, ValueError, TypeError, JSONDecodeError):
            self.__clearSecrets()
            return False
        return True

    # TODO temporary
    def deriveBlockDeviceKey(self) -> bytes | None:
        key1 = self._getKey(KeyIndex.WALLET_DATABASE)
        key2 = self._getKey(KeyIndex.SEED)
        if not key1 or not key2:
            return None
        assert len(key1) + len(key2) == 256 // 8
        return key1 + key2

    def deriveCipher(self, key_index: KeyIndex) -> AeadCipher | None:
        with self._lock:
            key = self._getKey(key_index)
            nonce = self._getNonce(key_index)
            if key is None or nonce is None:
                return None
            return AeadCipher(key, nonce)

    def deriveMessageCipher(self, key_index: KeyIndex) -> MessageCipher | None:
        with self._lock:
            key = self._getKey(key_index)
            if key is None:
                return None
            return MessageCipher(key)

    def reset(self) -> bool:
        with self._lock:
            self._clear()
            if self._config and not self._config.clear():
                return False
        return True


class _KeyStoreSeed(_KeyStoreBase):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__has_seed = False

    def _clear(self) -> None:
        super()._clear()
        self.__has_seed = False

    def _saveSeed(self, language: str, phrase: str, password: str) -> bool:
        if Product.STRING_SEPARATOR in language:
            return False
        if not self._config:
            return False

        cipher = self.deriveMessageCipher(KeyIndex.SEED)
        if cipher is None:
            return False

        seed = Mnemonic.phraseToSeed(phrase, password)
        seed = cipher.encrypt(seed)

        phrase = Product.STRING_SEPARATOR.join((language, phrase))
        phrase = cipher.encrypt(phrase.encode(Product.ENCODING))

        with self._config.lock:
            if not self._config.set(
                self._config.Key.SEED,
                seed,
                save=False,
            ):
                return False
            if not self._config.set(
                self._config.Key.SEED_PHRASE,
                phrase,
                save=False,
            ):
                return False
            return self._config.save()

    def __deriveSeed(self) -> bytes | None:
        if not self._config:
            return None
        value = self._config.get(self._config.Key.SEED, str)
        if not value:
            return None
        cipher = self.deriveMessageCipher(KeyIndex.SEED)
        if cipher is None:
            return None
        return cipher.decrypt(value)

    def _deriveSeedPhrase(self) -> Union[tuple[str, str], tuple[None, None]]:
        if not self._config:
            return None, None
        value = self._config.get(self._config.Key.SEED_PHRASE, str)
        if not value:
            return None, None

        cipher = self.deriveMessageCipher(KeyIndex.SEED)
        if cipher is None:
            return None, None

        value = cipher.decrypt(value)
        try:
            value = value.decode(Product.ENCODING)
            (language, phrase) = value.split(Product.STRING_SEPARATOR, 1)
        except (UnicodeError, ValueError):
            return None, None

        language = language.lower()
        phrase = Mnemonic.friendlyPhrase(language, phrase)
        return language, phrase

    def _deriveRootHdNodeFromSeed(self) -> HdNode | KeyStoreError | None:
        self.__has_seed = False

        seed = self.__deriveSeed()
        if not seed:
            return None

        root_node = HdNode.deriveRootNode(seed)
        if root_node is None:
            return KeyStoreError.ERROR_DERIVE_ROOT_HD_NODE
        self.__has_seed = True
        return root_node

    @property
    def hasSeed(self) -> bool:
        with self._lock:
            return self.__has_seed


class KeyStore(_KeyStoreSeed):
    def __init__(
        self,
        application: CoreApplication,
        *,
        open_callback: Callable[[HdNode | None], None],
        reset_callback: Callable[[], None],
    ) -> None:
        super().__init__(application)
        self._open_callback = open_callback
        self._reset_callback = reset_callback

    @property
    def isExists(self) -> bool:
        with self._lock:
            if self._config and self._config.get(self._config.Key.VALUE, str):
                return True
        return False

    def create(self, password: str) -> bool:
        if not self._config:
            return False
        value = self._generateSecretStoreValue()
        value = SecretStore(password).encryptValue(value)
        with self._lock:
            self.reset()
            return self._config.set(self._config.Key.VALUE, value)

    def verify(self, password: str) -> bool:
        if not self._config:
            return False
        with self._lock:
            value = self._config.get(self._config.Key.VALUE, str)
            if value and SecretStore(password).decryptValue(value):
                return True
        return False

    def open(self, password: str) -> KeyStoreError:
        with self._lock:
            self._clear()

            if not self._config:
                return KeyStoreError.ERROR_SEED_NOT_FOUND
            value = self._config.get(self._config.Key.VALUE, str)
            if not value:
                return KeyStoreError.ERROR_SEED_NOT_FOUND
            value = SecretStore(password).decryptValue(value)
            if not value:
                return KeyStoreError.ERROR_INVALID_PASSWORD
            if not self._loadSecretStoreValue(value):
                return KeyStoreError.ERROR_SEED_NOT_FOUND
            root_node = self._deriveRootHdNodeFromSeed()
            if isinstance(root_node, KeyStoreError):
                return root_node
            self._open_callback(root_node)
        return KeyStoreError.SUCCESS

    def saveSeed(
        self,
        language: str,
        phrase: str,
        key_store_password: str,
        name: str,
        seed_password: str,
    ) -> KeyStoreError:
        with self._lock:
            if not self._config.create(self._application.walletsPath, name):
                return KeyStoreError.ERROR_SAVE_SEED
            if not self.create(key_store_password):
                return KeyStoreError.ERROR_SAVE_SEED
            if not self.open(key_store_password):
                return KeyStoreError.ERROR_INVALID_PASSWORD

            result = self._saveSeed(language, phrase, seed_password)

            if not result:
                return KeyStoreError.ERROR_SAVE_SEED
            root_node = self._deriveRootHdNodeFromSeed()
            if root_node is None:
                return KeyStoreError.ERROR_SEED_NOT_FOUND
            if isinstance(root_node, KeyStoreError):
                return root_node
            self._open_callback(root_node)
        return KeyStoreError.SUCCESS

    def revealSeedPhrase(self, password: str) -> Union[KeyStoreError, str]:
        with self._lock:
            if not self.verify(password):
                return KeyStoreError.ERROR_INVALID_PASSWORD
            language, phrase = self._deriveSeedPhrase()
            if not language or not phrase:
                return KeyStoreError.ERROR_SEED_NOT_FOUND
            return phrase

    def reset(self) -> bool:
        with self._lock:
            if not super().reset():
                return False
            self._reset_callback()
        return True

    def close(self) -> None:
        pass


class _AbstractSeedPhrase:
    def __init__(self, key_store: KeyStore) -> None:
        self._key_store = key_store
        self._mnemonic: Mnemonic | None = None

    @property
    def inProgress(self) -> bool:
        return self._mnemonic is not None

    def clear(self) -> None:
        self._mnemonic = None

    def prepare(self, language: str = None) -> str:
        raise NotImplementedError

    def validate(self, phrase: str) -> bool:
        raise NotImplementedError

    def finalize(
        self,
        phrase: str,
        key_store_password: str,
        name: str,
        seed_password: str,
    ) -> KeyStoreError:
        if not self.validate(phrase):
            return KeyStoreError.ERROR_INVALID_SEED_PHRASE

        result = self._key_store.saveSeed(
            self._mnemonic.language,
            phrase,
            key_store_password,
            name,
            seed_password,
        )
        if result != KeyStoreError.SUCCESS:
            return result

        self.clear()
        return KeyStoreError.SUCCESS


class GenerateSeedPhrase(_AbstractSeedPhrase):
    def __init__(self, key_store: KeyStore) -> None:
        super().__init__(key_store)
        self._salt_hash: AbstractDigest | None = None

    def clear(self) -> None:
        super().clear()
        self._salt_hash = None

    def prepare(self, language: str = None) -> str:
        self._mnemonic = Mnemonic(language)
        self._salt_hash = Sha256Digest()
        self._salt_hash.update(os.urandom(64))

        result = self._salt_hash.copy().finalize()
        result = result[: Mnemonic.defaultDataLength]
        return self._mnemonic.getPhrase(result)

    def validate(self, phrase: str) -> bool:
        return (
            phrase
            and self.inProgress
            and Mnemonic.isEqualPhrases(phrase, self.update(None))
        )

    def update(self, salt: str | None) -> str:
        if not self.inProgress:
            return ""

        if salt:
            self._salt_hash.update(salt.encode(Product.ENCODING))
            self._salt_hash.update(os.urandom(4))

        result = self._salt_hash.copy().finalize()
        result = result[: Mnemonic.defaultDataLength]
        return self._mnemonic.getPhrase(result)


class RestoreSeedPhrase(_AbstractSeedPhrase):
    def prepare(self, language: str = None) -> bool:
        self._mnemonic = Mnemonic(language)
        return True

    def validate(self, phrase: str) -> bool:
        return (
            phrase and self.inProgress and self._mnemonic.isValidPhrase(phrase)
        )
