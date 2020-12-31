# JOK+
import os
import time
from unittest import TestCase

from bmnclient.crypto.cipher import MessageCipher
from bmnclient.crypto.kdf import KeyDerivationFunction
from bmnclient.crypto.password import PasswordStrength


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
        kdf = KeyDerivationFunction()
        kdf.setPassword(os.urandom(16).hex())
        for key_length in self.KEY_LENGTH_LIST:
            key = kdf.derive(b"salt1", key_length // 8)
            self.assertIsInstance(key, bytes)
            self.assertEqual(len(key), key_length // 8)

    def test_secret(self) -> None:
        kdf1 = KeyDerivationFunction()
        kdf1.setPassword(os.urandom(16).hex())
        kdf2 = KeyDerivationFunction()
        kdf2.setPassword(os.urandom(16).hex())

        secret1 = kdf1.createSecret(b"secret1")
        self.assertIsInstance(secret1, str)
        self.assertGreater(len(secret1), 10)
        self.assertTrue(secret1.startswith("v1:"))

        self.assertEqual(kdf1.verifySecret(secret1), b"secret1")
        self.assertEqual(kdf2.verifySecret(secret1), None)

    def test_bruteforce(self) -> None:
        password = os.urandom(4).hex()
        kdf = KeyDerivationFunction()
        kdf.setPassword(password)

        timeframe = time.monotonic_ns()
        kdf.derive(b"SALT", 128)
        timeframe = time.monotonic_ns() - timeframe

        result = (24 * 60 * 60 * 1e+9) / timeframe
        print(
            "KDF bruteforce status: ~{:.2f} combinations per day."
            .format(result))


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
            ("słowo", {
                "upper": False,
                "lower": True,
                "numbers": False,
                "special": False}),
            ("SŁOWO", {
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
            ("Реч@1", {
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
