# JOK+
import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase

from bmnclient.config import UserConfig
from bmnclient.key_store import KeyIndex, KeyStore
from bmnclient.version import Product
from bmnclient.wallet.mnemonic import Mnemonic
from tests import getLogger

_logger = getLogger(__name__)


class TestKeyStore(TestCase):
    def setUp(self) -> None:
        self.password = "123123Qaz"
        self.user_config_path = \
            Path(tempfile.gettempdir()) / (Product.SHORT_NAME + "-config.json")
        if self.user_config_path.exists():
            self.user_config_path.unlink()
        self.user_config = UserConfig(self.user_config_path)
        self.assertFalse(self.user_config.load())

    def tearDown(self) -> None:
        if self.user_config_path.exists():
            self.user_config_path.unlink()
        self.user_config = None

    def test_secret_store_value(self) -> None:
        key_store = KeyStore(self.user_config)
        self.assertEqual(len(KeyIndex), len(key_store._nonce_list))
        self.assertEqual(len(KeyIndex), len(key_store._key_list))

        for k in KeyIndex:
            self.assertIsNone(key_store._getNonce(k))

        value = KeyStore._generateSecretStoreValue()
        self.assertIsInstance(value, bytes)

        json_value = json.loads(value.decode(encoding=Product.ENCODING))
        self.assertIsInstance(json_value, dict)

        self.assertTrue(key_store._loadSecretStoreValue(value))

        for k in KeyIndex:
            self.assertIsInstance(key_store._getNonce(k), bytes)
            self.assertIsInstance(key_store._getKey(k), bytes)

    def test_password(self) -> None:
        key_store = KeyStore(self.user_config)

        self.assertFalse(key_store.hasPassword)
        self.assertIsNone(
            self.user_config.get(UserConfig.KEY_KEY_STORE_VALUE, str))
        self.assertTrue(key_store.createPassword(self.password))
        self.assertIsInstance(
            self.user_config.get(UserConfig.KEY_KEY_STORE_VALUE, str),
            str)
        self.assertTrue(key_store.hasPassword)

        for i in range(len(KeyIndex)):
            self.assertIsNone(key_store._nonce_list[i])
            self.assertIsNone(key_store._key_list[i])
        self.assertFalse(key_store.applyPassword(self.password * 2))
        for i in range(len(KeyIndex)):
            self.assertIsNone(key_store._nonce_list[i])
            self.assertIsNone(key_store._key_list[i])
        self.assertTrue(key_store.applyPassword(self.password))
        for i in range(len(KeyIndex)):
            self.assertIsInstance(key_store._nonce_list[i], bytes)
            self.assertIsInstance(key_store._key_list[i], bytes)

        for k in KeyIndex:
            self.assertIsInstance(key_store._getNonce(k), bytes)
            self.assertIsInstance(key_store._getKey(k), bytes)

        self.assertTrue(key_store.resetPassword())
        self.assertFalse(key_store.hasPassword)
        for i in range(len(KeyIndex)):
            self.assertIsNone(key_store._nonce_list[i])
            self.assertIsNone(key_store._key_list[i])
        self.assertIsNone(
            self.user_config.get(UserConfig.KEY_KEY_STORE_VALUE, str))

    def test_generate_seed_phrase(self) -> None:
        key_store = KeyStore(self.user_config)
        self.assertFalse(key_store.hasPassword)
        self.assertTrue(key_store.createPassword(self.password))
        self.assertTrue(key_store.applyPassword(self.password))
        self.assertIsNone(key_store._getSeed())

        for language in Mnemonic.getLanguageList():
            phrase1 = key_store.prepareGenerateSeedPhrase(language)
            self.assertTrue(Mnemonic(language).isValidPhrase(phrase1))
            self.assertTrue(key_store.validateGenerateSeedPhrase(phrase1))

            phrase2 = key_store.updateGenerateSeedPhrase("123")
            self.assertTrue(Mnemonic(language).isValidPhrase(phrase2))
            self.assertTrue(key_store.validateGenerateSeedPhrase(phrase2))
            self.assertNotEqual(phrase1, phrase2)
            self.assertFalse(Mnemonic.isEqualPhrases(phrase1, phrase2))
            self.assertFalse(key_store.validateGenerateSeedPhrase(phrase1))

            seed2 = key_store._mnemonic.phraseToSeed(phrase2)
            self.assertIsInstance(seed2, bytes)

            self.assertFalse(key_store.finalizeGenerateSeedPhrase(phrase1))
            self.assertTrue(key_store.finalizeGenerateSeedPhrase(phrase2))
            self.assertIsNone(key_store._mnemonic)
            self.assertIsNone(key_store._mnemonic_salt_hash)

            result = key_store._getSeed()
            self.assertIsInstance(result, bytes)
            self.assertEqual(seed2, result)

            result = key_store._getSeedPhrase()
            self.assertIsInstance(result, tuple)
            self.assertIsInstance(result[0], str)
            self.assertIsInstance(result[1], str)
            self.assertEqual(language, result[0])
            self.assertEqual(phrase2, result[1])

    def test_restore_seed_phrase(self) -> None:
        key_store = KeyStore(self.user_config)
        self.assertFalse(key_store.hasPassword)
        self.assertTrue(key_store.createPassword(self.password))
        self.assertTrue(key_store.applyPassword(self.password))

        for language in Mnemonic.getLanguageList():
            phrase = Mnemonic(language).getPhrase(os.urandom(24))
            self.assertGreater(len(phrase), 0)

            self.assertFalse(key_store.validateRestoreSeedPhrase(phrase))
            self.assertTrue(key_store.prepareRestoreSeedPhrase(language))
            self.assertTrue(key_store.validateRestoreSeedPhrase(phrase))
            self.assertTrue(key_store.finalizeRestoreSeedPhrase(phrase))
            self.assertIsNone(key_store._mnemonic)
            self.assertIsNone(key_store._mnemonic_salt_hash)

            seed = key_store._getSeed()
            self.assertIsInstance(seed, bytes)
            self.assertEqual(Mnemonic(language).phraseToSeed(phrase), seed)

            result = key_store._getSeedPhrase()
            self.assertIsInstance(result, tuple)
            self.assertIsInstance(result[0], str)
            self.assertIsInstance(result[1], str)
            self.assertEqual(language, result[0])
            self.assertEqual(phrase, result[1])
