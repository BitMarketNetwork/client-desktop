# JOK+
import json
import tempfile
from pathlib import Path
from unittest import TestCase

from bmnclient import version
from bmnclient.config import UserConfig
from bmnclient.crypto.kdf import KeyDerivationFunction
from bmnclient.key_store import KeyType, Secret, KeyStore


class TestSecret(TestCase):
    def test_basic(self) -> None:
        secret = Secret()
        self.assertEqual(len(KeyType), len(secret._nonce_list))

        for k in KeyType:
            self.assertIsNone(secret.getNonce(k))

        value = Secret.generate()
        self.assertIsInstance(value, bytes)

        json_value = json.loads(value.decode(encoding=version.ENCODING))
        self.assertIsInstance(json_value, dict)

        self.assertTrue(secret.load(value))

        for k in KeyType:
            self.assertIsInstance(secret.getNonce(k), bytes)


class TestKeyStore(TestCase):
    def setUp(self) -> None:
        self.password = "123123Qaz"
        self.user_config_path = \
            Path(tempfile.gettempdir()) / (version.SHORT_NAME + "-config.json")
        if self.user_config_path.exists():
            self.user_config_path.unlink()
        self.user_config = UserConfig(self.user_config_path)
        self.assertFalse(self.user_config.load())

    def tearDown(self) -> None:
        if self.user_config_path.exists():
            self.user_config_path.unlink()
        self.user_config = None

    def test_password(self) -> None:
        key_store = KeyStore(self.user_config)

        self.assertFalse(key_store.hasPassword)
        self.assertIsNone(
            self.user_config.get(UserConfig.KEY_WALLET_SECRET, str))
        self.assertTrue(key_store.createPassword(self.password))
        self.assertIsInstance(
            self.user_config.get(UserConfig.KEY_WALLET_SECRET, str),
            str)
        self.assertTrue(key_store.hasPassword)

        self.assertIsNone(key_store._kdf)
        self.assertIsNone(key_store._secret)
        self.assertFalse(key_store.setPassword(self.password * 2))
        self.assertIsNone(key_store._kdf)
        self.assertIsNone(key_store._secret)
        self.assertTrue(key_store.setPassword(self.password))
        self.assertIsInstance(key_store._kdf, KeyDerivationFunction)
        self.assertIsInstance(key_store._secret, Secret)

        for k in KeyType:
            self.assertIsInstance(key_store._secret.getNonce(k), bytes)

        self.assertTrue(key_store.resetPassword())
        self.assertFalse(key_store.hasPassword)
        self.assertIsNone(key_store._kdf)
        self.assertIsNone(key_store._secret)
        self.assertIsNone(
            self.user_config.get(UserConfig.KEY_WALLET_SECRET, str))
