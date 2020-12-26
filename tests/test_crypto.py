import os
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
        kdf.setPassphrase(os.urandom(16).hex())
        for key_length in self.KEY_LENGTH_LIST:
            key = kdf.derive(b"salt1", key_length // 8)
            self.assertIsInstance(key, bytes)
            self.assertEqual(len(key), key_length // 8)

    def test_secret(self) -> None:
        kdf1 = KeyDerivationFunction()
        kdf1.setPassphrase(os.urandom(16).hex())
        kdf2 = KeyDerivationFunction()
        kdf2.setPassphrase(os.urandom(16).hex())

        secret1 = kdf1.createSecret()
        self.assertIsInstance(secret1, str)
        self.assertGreater(len(secret1), 10)
        self.assertTrue(secret1.startswith("v1:"))

        self.assertTrue(kdf1.verifySecret(secret1))
        self.assertFalse(kdf2.verifySecret(secret1))
