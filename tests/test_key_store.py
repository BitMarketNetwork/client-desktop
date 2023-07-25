import json
import os
from unittest import TestCase

from bmnclient.coins.hd import HdNode
from bmnclient.coins.mnemonic import Mnemonic
from bmnclient.config import KeyStoreConfig
from bmnclient.crypto.cipher import AeadCipher, MessageCipher
from bmnclient.crypto.digest import Sha256Digest
from bmnclient.key_store import (
    GenerateSeedPhrase,
    KeyIndex,
    KeyStore,
    KeyStoreError,
    RestoreSeedPhrase,
)
from bmnclient.version import Product
from tests.helpers import TestApplication

_logger = TestApplication.getLogger(__name__)


class TestKeyStore(TestCase):
    def setUp(self) -> None:
        self._password = "123123Qaz"
        self._application = TestApplication()

    def tearDown(self) -> None:
        self._application.setExitEvent()

    def assertKeysIsNone(self, key_store: KeyStore) -> None:
        for k in KeyIndex:
            self.assertIsNone(key_store._getNonce(k))
            self.assertIsNone(key_store._getKey(k))
            self.assertIsNone(key_store.deriveCipher(k))
            self.assertIsNone(key_store.deriveMessageCipher(k))

    def assertKeysIsValid(self, key_store: KeyStore) -> None:
        for k in KeyIndex:
            self.assertIsInstance(key_store._getNonce(k), bytes)
            self.assertIsInstance(key_store._getKey(k), bytes)
            self.assertIsInstance(key_store.deriveCipher(k), AeadCipher)
            self.assertIsInstance(
                key_store.deriveMessageCipher(k), MessageCipher
            )

    def test_secret_store_value(self) -> None:
        key_store = KeyStore(
            self._application,
            open_callback=lambda *_: None,
            reset_callback=lambda *_: None,
        )
        key_store.config = KeyStoreConfig(
            self._application.tempPath / "key_store59.json"
        )
        self.assertEqual(
            len(KeyIndex), len(key_store._KeyStoreBase__nonce_list)
        )
        self.assertEqual(len(KeyIndex), len(key_store._KeyStoreBase__key_list))

        self.assertKeysIsNone(key_store)

        value = key_store._generateSecretStoreValue()
        self.assertIsInstance(value, bytes)

        json_value = json.loads(value.decode(Product.ENCODING))
        self.assertIsInstance(json_value, dict)

        self.assertTrue(key_store._loadSecretStoreValue(value))
        self.assertKeysIsValid(key_store)

        self.assertFalse(key_store._loadSecretStoreValue(b"broken" + value))
        self.assertKeysIsNone(key_store)

    def test_seed(self) -> None:
        key_store = KeyStore(
            self._application,
            open_callback=lambda *_: None,
            reset_callback=lambda *_: None,
        )
        key_store.config = KeyStoreConfig(
            self._application.tempPath / "key_store91.json"
        )

        self.assertFalse(key_store.hasSeed)
        self.assertIsNone(key_store._KeyStoreSeed__deriveSeed())
        self.assertTupleEqual((None, None), key_store._deriveSeedPhrase())
        self.assertIsNone(key_store._deriveRootHdNodeFromSeed())
        self.assertFalse(key_store.hasSeed)

        for language in Mnemonic.getLanguageList():
            phrase_hash = Sha256Digest(os.urandom(64)).finalize()
            phrase_hash = phrase_hash[: Mnemonic.defaultDataLength]
            phrase = Mnemonic(language).getPhrase(phrase_hash)
            self.assertLess(1, len(phrase))
            seed = Mnemonic.phraseToSeed(phrase)
            self.assertLess(1, len(seed))
            self.assertFalse(key_store._saveSeed(language, phrase, ""))

            value = key_store._generateSecretStoreValue()
            self.assertIsInstance(value, bytes)
            self.assertTrue(key_store._loadSecretStoreValue(value))
            self.assertKeysIsValid(key_store)

            self.assertIsNone(
                key_store.config.get(key_store.config.Key.SEED, str)
            )
            self.assertIsNone(
                key_store.config.get(key_store.config.Key.SEED_PHRASE, str)
            )
            self.assertTrue(key_store._saveSeed(language, phrase, ""))
            self.assertIsInstance(
                key_store.config.get(key_store.config.Key.SEED, str), str
            )
            self.assertIsInstance(
                key_store.config.get(key_store.config.Key.SEED_PHRASE, str),
                str,
            )

            self.assertEqual(seed, key_store._KeyStoreSeed__deriveSeed())
            self.assertTupleEqual(
                (language, phrase), key_store._deriveSeedPhrase()
            )
            self.assertIsInstance(
                key_store._deriveRootHdNodeFromSeed(), HdNode
            )
            self.assertTrue(key_store.hasSeed)

            self.assertTrue(key_store.reset())
            self.assertFalse(key_store.hasSeed)
            self.assertIsNone(key_store._KeyStoreSeed__deriveSeed())
            self.assertKeysIsNone(key_store)

    def test(self) -> None:
        key_store = KeyStore(
            self._application,
            open_callback=lambda *_: None,
            reset_callback=lambda *_: None,
        )
        key_store_config = KeyStoreConfig(
            self._application.tempPath / "key_store156.json"
        )

        self.assertFalse(key_store.isExists)
        self.assertIsNone(key_store.config)
        self.assertFalse(key_store.create(self._password))
        self.assertTrue(key_store.reset())

        key_store.config = key_store_config

        self.assertTrue(key_store.create(self._password))
        self.assertTrue(key_store.isExists)
        self.assertIsInstance(
            key_store.config.get(key_store.config.Key.VALUE, str),
            str,
        )
        self.assertKeysIsNone(key_store)
        self.assertFalse(key_store.hasSeed)

        self.assertFalse(key_store.verify(self._password * 2))
        self.assertEqual(
            key_store.open(self._password * 2),
            KeyStoreError.ERROR_INVALID_PASSWORD,
        )
        self.assertKeysIsNone(key_store)
        self.assertFalse(key_store.hasSeed)

        self.assertTrue(key_store.verify(self._password))
        self.assertEqual(key_store.open(self._password), KeyStoreError.SUCCESS)
        self.assertKeysIsValid(key_store)
        self.assertFalse(key_store.hasSeed)

        self.assertTrue(key_store.reset())
        self.assertIsNone(
            key_store.config.get(key_store.config.Key.VALUE, str)
        )

    def test_generate_seed_phrase(self) -> None:
        key_store = KeyStore(
            self._application,
            open_callback=lambda *_: None,
            reset_callback=lambda *_: None,
        )
        key_store.config = KeyStoreConfig(
            self._application.tempPath / "key_store200.json"
        )

        self.assertFalse(key_store.isExists)
        self.assertTrue(key_store.create(self._password))
        self.assertEqual(key_store.open(self._password), KeyStoreError.SUCCESS)
        self.assertFalse(key_store.hasSeed)

        self.assertEqual(
            KeyStoreError.ERROR_INVALID_PASSWORD,
            key_store.revealSeedPhrase(self._password * 2),
        )
        self.assertEqual(
            KeyStoreError.ERROR_SEED_NOT_FOUND,
            key_store.revealSeedPhrase(self._password),
        )

        for language in Mnemonic.getLanguageList():
            g1 = GenerateSeedPhrase(key_store)
            phrase1 = g1.prepare(language)
            self.assertTrue(Mnemonic(language).isValidPhrase(phrase1))
            self.assertTrue(g1.validate(phrase1))

            phrase2 = g1.update(os.urandom(10).hex())
            self.assertTrue(Mnemonic(language).isValidPhrase(phrase2))
            self.assertTrue(g1.validate(phrase2))
            self.assertNotEqual(phrase1, phrase2)
            self.assertFalse(Mnemonic.isEqualPhrases(phrase1, phrase2))
            self.assertFalse(g1.validate(phrase1))

            seed2 = g1._mnemonic.phraseToSeed(phrase2)
            self.assertIsInstance(seed2, bytes)

            self.assertEqual(
                g1.finalize(phrase1, self._password, "", ""),
                KeyStoreError.ERROR_INVALID_SEED_PHRASE,
            )
            self.assertEqual(
                g1.finalize(phrase2, self._password, "", ""),
                KeyStoreError.SUCCESS,
            )
            self.assertTrue(key_store.hasSeed)

            result = key_store._KeyStoreSeed__deriveSeed()
            self.assertIsInstance(result, bytes)
            self.assertEqual(seed2, result)

            result = key_store._deriveSeedPhrase()
            self.assertIsInstance(result, tuple)
            self.assertIsInstance(result[0], str)
            self.assertIsInstance(result[1], str)
            self.assertEqual(language, result[0])
            self.assertEqual(phrase2, result[1])

            self.assertEqual(
                KeyStoreError.ERROR_INVALID_PASSWORD,
                key_store.revealSeedPhrase(self._password * 2),
            )
            self.assertEqual(
                phrase2,
                key_store.revealSeedPhrase(self._password),
            )

    def test_restore_seed_phrase(self) -> None:
        key_store = KeyStore(
            self._application,
            open_callback=lambda *_: None,
            reset_callback=lambda *_: None,
        )
        key_store.config = KeyStoreConfig(
            self._application.tempPath / "key_store300.json"
        )

        self.assertFalse(key_store.isExists)
        self.assertTrue(key_store.create(self._password))
        self.assertEqual(
            key_store.open(self._password),
            KeyStoreError.SUCCESS,
        )

        for language in Mnemonic.getLanguageList():
            r1 = RestoreSeedPhrase(key_store)
            phrase = Mnemonic(language).getPhrase(os.urandom(24))
            self.assertLess(0, len(phrase))

            self.assertFalse(r1.validate(phrase))
            self.assertTrue(r1.prepare(language))
            self.assertTrue(r1.validate(phrase))
            self.assertEqual(
                r1.finalize(phrase, self._password, "", ""),
                KeyStoreError.SUCCESS,
            )
            self.assertTrue(key_store.hasSeed)

            seed = Mnemonic.phraseToSeed(phrase)
            self.assertIsInstance(seed, bytes)
            self.assertEqual(Mnemonic(language).phraseToSeed(phrase), seed)

            result = key_store._deriveSeedPhrase()
            self.assertIsInstance(result, tuple)
            self.assertIsInstance(result[0], str)
            self.assertIsInstance(result[1], str)
            self.assertEqual(language, result[0])
            self.assertEqual(phrase, result[1])
