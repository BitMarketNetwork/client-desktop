import os
import time
from unittest import TestCase

from bmnclient.crypto.cipher import MessageCipher
from bmnclient.crypto.kdf import KeyDerivationFunction


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
