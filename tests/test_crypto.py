# JOK4
import os
import time
from unittest import TestCase

from bmnclient.crypto.cipher import MessageCipher
from bmnclient.crypto.kdf import KeyDerivationFunction, SecretStore
from bmnclient.crypto.password import PasswordStrength
from . import TestApplication

_logger = TestApplication.getLogger(__name__)


class TestMessageCipher(TestCase):
    def test_basic(self) -> None:
        for data_size in (1, 2, 3, 128, 1000, 4096, 65000, 65536):
            key = MessageCipher.generateKey()
            source_text = os.urandom(data_size)
            mc1 = MessageCipher(key)
            mc2 = MessageCipher(key)

            cipher_text = mc1.encrypt(source_text)

            self.assertGreater(len(cipher_text), 0)
            self.assertIsInstance(cipher_text, str)
            self.assertEqual(len(cipher_text.split(":")), 2)
            self.assertGreater(len(cipher_text.split(":")[0]), 0)
            self.assertGreater(len(cipher_text.split(":")[1]), 0)

            plain_text = mc1.decrypt(cipher_text)
            self.assertEqual(plain_text, source_text)
            self.assertEqual(mc2.decrypt(cipher_text), source_text)

            self.assertEqual(mc1.decrypt(cipher_text, "@"), None)

            cipher_text = mc1.encrypt(source_text, "@")
            self.assertEqual(mc1.decrypt(cipher_text, "@"), source_text)


class TestKdf(TestCase):
    KEY_LENGTH_LIST = (128, 256)

    def test_basic(self) -> None:
        for key_length in self.KEY_LENGTH_LIST:
            kdf = KeyDerivationFunction(os.urandom(16).hex())
            key = kdf.derive(b"salt1", key_length // 8)
            self.assertIsInstance(key, bytes)
            self.assertEqual(len(key), key_length // 8)

    def test_bruteforce(self) -> None:
        password = os.urandom(4).hex()
        kdf = KeyDerivationFunction(password)

        timeframe = time.monotonic_ns()
        kdf.derive(b"salt2", 128)
        timeframe = time.monotonic_ns() - timeframe

        result = (24 * 60 * 60 * 1e+9) / timeframe
        _logger.info(
            "KDF bruteforce status: ~{:.2f} combinations per day."
            .format(result))


class TestSecretStore(TestCase):
    def test_basic(self) -> None:
        store1 = SecretStore(os.urandom(16).hex())
        store2 = SecretStore(os.urandom(16).hex())

        value1 = store1.encryptValue(b"secret1")
        self.assertIsInstance(value1, str)
        self.assertGreater(len(value1), 10)
        self.assertTrue(value1.startswith("v1:"))

        self.assertEqual(store1.decryptValue(value1), b"secret1")
        self.assertEqual(store2.decryptValue(value1), None)

        self.assertEqual(store1.decryptValue("v2" + value1[:2]), None)
        self.assertEqual(store1.decryptValue("v1"), None)
        self.assertEqual(store1.decryptValue(""), None)
        self.assertEqual(store1.decryptValue(":::::"), None)
        self.assertEqual(store1.decryptValue("1:2:3:4:5:6"), None)


class TestPassword(TestCase):
    def test_char_groups(self) -> None:
        password_list = (
            ("",  {
                "upper": False,
                "lower": False,
                "numbers": False,
                "special": False}),
            ("A", {
                "upper": True,
                "lower": False,
                "numbers": False,
                "special": False}),
            ("a", {
                "upper": False,
                "lower": True,
                "numbers": False,
                "special": False}),
            ("Aa", {
                "upper": True,
                "lower": True,
                "numbers": False,
                "special": False}),
            ("1", {
                "upper": False,
                "lower": False,
                "numbers": True,
                "special": False}),
            ("Aa1", {
                "upper": True,
                "lower": True,
                "numbers": True,
                "special": False}),
            (".", {
                "upper": False,
                "lower": False,
                "numbers": False,
                "special": True}),
            (" ", {
                "upper": False,
                "lower": False,
                "numbers": False,
                "special": True}),
            ("słowo", {  # noqa
                "upper": False,
                "lower": True,
                "numbers": False,
                "special": False}),
            ("SŁOWO", { # noqa
                "upper": True,
                "lower": False,
                "numbers": False,
                "special": False}),
            ("реч", {
                "upper": False,
                "lower": True,
                "numbers": False,
                "special": False}),
            ("РЕЧ", {
                "upper": True,
                "lower": False,
                "numbers": False,
                "special": False}),
            ("Реч@1", { # noqa
                "upper": True,
                "lower": True,
                "numbers": True,
                "special": True}),
            ("`", {
                "upper": False,
                "lower": False,
                "numbers": False,
                "special": True}),
        )
        for v in password_list:
            # noinspection PyProtectedMember
            s = PasswordStrength(v[0])._getCharGroups()
            self.assertEqual(s, v[1])

    def test_strength(self) -> None:
        password_list = (
            ("1", 1),
            ("111122223333", 2),
            ("12345678", 1),
            ("1234567a", 2),
            ("123456aA", 3),
            ("12345aA@", 4),
            ("12345aA@@@@@@@@@@", 5),
            ("1234@aABCDEFGHIJ", 5),
            ("1234@aABCDEFGHIJK", 6),
        )
        for v in password_list:
            s = PasswordStrength(v[0]).calc()
            self.assertEqual(s, v[1])
