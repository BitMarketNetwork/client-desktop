import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase

from bmnclient.coins.hd import HdNode
from bmnclient.coins.mnemonic import Mnemonic
from bmnclient.config import UserConfigKey
from bmnclient.crypto.cipher import AeadCipher, MessageCipher
from bmnclient.crypto.digest import Sha256Digest
from bmnclient.key_store import \
    KeyIndex, \
    KeyStore, \
    KeyStoreError, \
    SeedPhraseGenerate, \
    SeedPhraseRestore
from bmnclient.version import Product, ProductPaths
from tests import TestApplication

_logger = TestApplication.getLogger(__name__)


class TestKeyStore(TestCase):
    def setUp(self) -> None:
        self._password = "123123Qaz"
        self._user_config_path = \
            Path(tempfile.gettempdir()) \
            / (Product.SHORT_NAME + "-" + self.__class__.__name__) \
            / ProductPaths.CONFIG_FILE_NAME
        if self._user_config_path.exists():
            self._user_config_path.unlink()

        self._application = TestApplication(
            config_path=str(self._user_config_path.parent))
        self.assertEqual(
            str(self._user_config_path),
            str(self._application.userConfig.filePath))
        self.assertFalse(self._application.userConfig.load())

    def tearDown(self) -> None:
        self._application.setExitEvent()
        if self._user_config_path.exists():
            self._user_config_path.unlink()

    def assertKeysIsNone(self, key_store: KeyStore) -> None:
        for k in KeyIndex:
            # noinspection PyProtectedMember
            self.assertIsNone(key_store._getNonce(k))
            # noinspection PyProtectedMember
            self.assertIsNone(key_store._getKey(k))
            self.assertIsNone(key_store.deriveCipher(k))
            self.assertIsNone(key_store.deriveMessageCipher(k))

    def assertKeysIsValid(self, key_store: KeyStore) -> None:
        for k in KeyIndex:
            # noinspection PyProtectedMember
            self.assertIsInstance(key_store._getNonce(k), bytes)
            # noinspection PyProtectedMember
            self.assertIsInstance(key_store._getKey(k), bytes)
            self.assertIsInstance(
                key_store.deriveCipher(k),
                AeadCipher)
            self.assertIsInstance(
                key_store.deriveMessageCipher(k),
                MessageCipher)

    def test_secret_store_value(self) -> None:
        key_store = KeyStore(
            self._application,
            open_callback=lambda *_: None,
            reset_callback=lambda *_: None)
        # noinspection PyProtectedMember
        self.assertEqual(
            len(KeyIndex),
            len(key_store._KeyStoreBase__nonce_list))
        # noinspection PyProtectedMember
        self.assertEqual(
            len(KeyIndex),
            len(key_store._KeyStoreBase__key_list))

        self.assertKeysIsNone(key_store)

        # noinspection PyProtectedMember
        value = key_store._generateSecretStoreValue()
        self.assertIsInstance(value, bytes)

        json_value = json.loads(value.decode(Product.ENCODING))
        self.assertIsInstance(json_value, dict)

        # noinspection PyProtectedMember
        self.assertTrue(key_store._loadSecretStoreValue(value))
        self.assertKeysIsValid(key_store)

        # noinspection PyProtectedMember
        self.assertFalse(key_store._loadSecretStoreValue(b"broken" + value))
        self.assertKeysIsNone(key_store)

    def test_seed(self) -> None:
        key_store = KeyStore(
            self._application,
            open_callback=lambda *_: None,
            reset_callback=lambda *_: None)

        self.assertFalse(key_store.hasSeed)
        # noinspection PyProtectedMember
        self.assertIsNone(key_store._KeyStoreSeed__deriveSeed())
        # noinspection PyProtectedMember
        self.assertTupleEqual(
            (None, None),
            key_store._deriveSeedPhrase())
        # noinspection PyProtectedMember
        self.assertIsNone(key_store._deriveRootHdNodeFromSeed())
        self.assertFalse(key_store.hasSeed)

        for language in Mnemonic.getLanguageList():
            phrase_hash = Sha256Digest(os.urandom(64)).finalize()
            phrase_hash = phrase_hash[:Mnemonic.defaultDataLength]
            phrase = Mnemonic(language).getPhrase(phrase_hash)
            self.assertLess(1, len(phrase))
            seed = Mnemonic.phraseToSeed(phrase)
            self.assertLess(1, len(seed))
            # noinspection PyProtectedMember
            self.assertFalse(key_store._saveSeed(language, phrase))

            # noinspection PyProtectedMember
            value = key_store._generateSecretStoreValue()
            self.assertIsInstance(value, bytes)
            # noinspection PyProtectedMember
            self.assertTrue(key_store._loadSecretStoreValue(value))
            self.assertKeysIsValid(key_store)

            self.assertIsNone(self._application.userConfig.get(
                UserConfigKey.KEY_STORE_SEED, str))
            self.assertIsNone(self._application.userConfig.get(
                UserConfigKey.KEY_STORE_SEED_PHRASE, str))
            # noinspection PyProtectedMember
            self.assertTrue(key_store._saveSeed(language, phrase))
            self.assertIsInstance(self._application.userConfig.get(
                UserConfigKey.KEY_STORE_SEED, str),
                str)
            self.assertIsInstance(self._application.userConfig.get(
                UserConfigKey.KEY_STORE_SEED_PHRASE, str),
                str)

            # noinspection PyProtectedMember
            self.assertEqual(
                seed,
                key_store._KeyStoreSeed__deriveSeed())
            # noinspection PyProtectedMember
            self.assertTupleEqual(
                (language, phrase),
                key_store._deriveSeedPhrase())
            # noinspection PyProtectedMember
            self.assertIsInstance(
                key_store._deriveRootHdNodeFromSeed(),
                HdNode)
            self.assertTrue(key_store.hasSeed)

            self.assertTrue(key_store.reset())
            self.assertFalse(key_store.hasSeed)
            # noinspection PyProtectedMember
            self.assertIsNone(key_store._KeyStoreSeed__deriveSeed())
            self.assertKeysIsNone(key_store)

    def test(self) -> None:
        key_store = KeyStore(
            self._application,
            open_callback=lambda *_: None,
            reset_callback=lambda *_: None)

        self.assertFalse(key_store.isExists)
        self.assertIsNone(self._application.userConfig.get(
            UserConfigKey.KEY_STORE_VALUE,
            str))

        self.assertTrue(key_store.create(self._password))
        self.assertTrue(key_store.isExists)
        self.assertIsInstance(
            self._application.userConfig.get(
                UserConfigKey.KEY_STORE_VALUE,
                str),
            str)
        self.assertKeysIsNone(key_store)
        self.assertFalse(key_store.hasSeed)

        self.assertFalse(key_store.verify(self._password * 2))
        self.assertFalse(key_store.open(self._password * 2))
        self.assertKeysIsNone(key_store)
        self.assertFalse(key_store.hasSeed)

        self.assertTrue(key_store.verify(self._password))
        self.assertTrue(key_store.open(self._password))
        self.assertKeysIsValid(key_store)
        self.assertFalse(key_store.hasSeed)

        self.assertTrue(key_store.reset())
        self.assertIsNone(self._application.userConfig.get(
            UserConfigKey.KEY_STORE_VALUE,
            str))

    def test_generate_seed_phrase(self) -> None:
        key_store = KeyStore(
            self._application,
            open_callback=lambda *_: None,
            reset_callback=lambda *_: None)

        self.assertFalse(key_store.isExists)
        self.assertTrue(key_store.create(self._password))
        self.assertTrue(key_store.open(self._password))
        self.assertFalse(key_store.hasSeed)

        self.assertEqual(
            KeyStoreError.ERROR_INVALID_PASSWORD,
            key_store.revealSeedPhrase(self._password * 2))
        self.assertEqual(
            KeyStoreError.ERROR_SEED_NOT_FOUND,
            key_store.revealSeedPhrase(self._password))

        for language in Mnemonic.getLanguageList():
            g1 = SeedPhraseGenerate(key_store)
            phrase1 = g1.prepare(language)
            self.assertTrue(Mnemonic(language).isValidPhrase(phrase1))
            self.assertTrue(g1.validate(phrase1))

            phrase2 = g1.update(os.urandom(10).hex())
            self.assertTrue(Mnemonic(language).isValidPhrase(phrase2))
            self.assertTrue(g1.validate(phrase2))
            self.assertNotEqual(phrase1, phrase2)
            self.assertFalse(Mnemonic.isEqualPhrases(phrase1, phrase2))
            self.assertFalse(g1.validate(phrase1))

            # noinspection PyProtectedMember
            seed2 = g1._mnemonic.phraseToSeed(phrase2)
            self.assertIsInstance(seed2, bytes)

            self.assertFalse(g1.finalize(phrase1))
            self.assertTrue(g1.finalize(phrase2))
            self.assertTrue(key_store.hasSeed)

            # noinspection PyProtectedMember
            result = key_store._KeyStoreSeed__deriveSeed()
            self.assertIsInstance(result, bytes)
            self.assertEqual(seed2, result)

            # noinspection PyProtectedMember
            result = key_store._deriveSeedPhrase()
            self.assertIsInstance(result, tuple)
            self.assertIsInstance(result[0], str)
            self.assertIsInstance(result[1], str)
            self.assertEqual(language, result[0])
            self.assertEqual(phrase2, result[1])

            self.assertEqual(
                KeyStoreError.ERROR_INVALID_PASSWORD,
                key_store.revealSeedPhrase(self._password * 2))
            self.assertEqual(
                phrase2,
                key_store.revealSeedPhrase(self._password))

    def test_restore_seed_phrase(self) -> None:
        key_store = KeyStore(
            self._application,
            open_callback=lambda *_: None,
            reset_callback=lambda *_: None)

        self.assertFalse(key_store.isExists)
        self.assertTrue(key_store.create(self._password))
        self.assertTrue(key_store.open(self._password))

        for language in Mnemonic.getLanguageList():
            r1 = SeedPhraseRestore(key_store)
            phrase = Mnemonic(language).getPhrase(os.urandom(24))
            self.assertLess(0, len(phrase))

            self.assertFalse(r1.validate(phrase))
            self.assertTrue(r1.prepare(language))
            self.assertTrue(r1.validate(phrase))
            self.assertTrue(r1.finalize(phrase))
            self.assertTrue(key_store.hasSeed)

            # noinspection PyProtectedMember
            seed = r1._mnemonic.phraseToSeed(phrase)
            self.assertIsInstance(seed, bytes)
            self.assertEqual(Mnemonic(language).phraseToSeed(phrase), seed)

            # noinspection PyProtectedMember
            result = key_store._deriveSeedPhrase()
            self.assertIsInstance(result, tuple)
            self.assertIsInstance(result[0], str)
            self.assertIsInstance(result[1], str)
            self.assertEqual(language, result[0])
            self.assertEqual(phrase, result[1])
