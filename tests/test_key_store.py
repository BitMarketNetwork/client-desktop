# JOK+
import json
import tempfile
from pathlib import Path
from unittest import TestCase

from bmnclient import version
from bmnclient.config import UserConfig
from bmnclient.key_store import KeyIndex, KeyStore


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

    def test_secret_store_value(self) -> None:
        key_store = KeyStore(self.user_config)
        self.assertEqual(len(KeyIndex), len(key_store._nonce_list))
        self.assertEqual(len(KeyIndex), len(key_store._key_list))

        for k in KeyIndex:
            self.assertIsNone(key_store._getNonce(k))

        value = KeyStore._generateSecretStoreValue()
        self.assertIsInstance(value, bytes)

        json_value = json.loads(value.decode(encoding=version.ENCODING))
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
        self.assertFalse(key_store.setPassword(self.password * 2))
        for i in range(len(KeyIndex)):
            self.assertIsNone(key_store._nonce_list[i])
            self.assertIsNone(key_store._key_list[i])
        self.assertTrue(key_store.setPassword(self.password))
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
