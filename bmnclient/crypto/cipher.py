# JOK+
import os
from typing import Optional

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers import aead

from .. import version


class Cipher:
    CIPHER = aead.AESGCM
    NONCE_LENGTH = 96 // 8  # NIST recommends
    ASSOCIATED_DATA = version.SHORT_NAME.encode(encoding=version.ENCODING)

    def __init__(self, key: bytes) -> None:
        self._cipher = self.CIPHER(key)

    @classmethod
    def generateKey(cls) -> bytes:
        return cls.CIPHER.generate_key(128)

    @classmethod
    def generateNonce(cls) -> bytes:
        return os.urandom(cls.NONCE_LENGTH)

    def encrypt(self, nonce: bytes, data: bytes) -> bytes:
        return self._cipher.encrypt(nonce, data, self.ASSOCIATED_DATA)

    def decrypt(self, nonce: bytes, data: bytes) -> Optional[bytes]:
        try:
            return self._cipher.decrypt(nonce, data, self.ASSOCIATED_DATA)
        except InvalidTag:
            return None


class MessageCipher(Cipher):
    def encrypt(self, data: bytes, separator: str = ":") -> str:
        nonce = self.generateNonce()
        cipher_text = super().encrypt(nonce, data)
        return nonce.hex() + separator + cipher_text.hex()

    def decrypt(self, text: str, separator: str = ":") -> Optional[bytes]:
        try:
            (nonce, data) = text.split(separator, 1)
            return super().decrypt(
                bytes.fromhex(nonce),
                bytes.fromhex(data))
        except (ValueError, TypeError):
            return None
