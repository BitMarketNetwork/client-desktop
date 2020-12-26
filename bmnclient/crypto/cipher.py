# JOK+
import os
from typing import Optional

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers import aead

from bmnclient import version


class MessageCipher:
    CIPHER = aead.AESGCM
    NONCE_LENGTH = 96 // 8  # NIST recommends
    ASSOCIATED_DATA = version.SHORT_NAME.encode(encoding="utf-8")

    def __init__(self, key: bytes) -> None:
        self._cipher = self.CIPHER(key)

    @classmethod
    def generateKey(cls) -> bytes:
        return cls.CIPHER.generate_key(128)

    def encrypt(self, data: bytes, separator: str = ":") -> Optional[str]:
        nonce = os.urandom(self.NONCE_LENGTH)
        cipher_text = self._cipher.encrypt(
            nonce,
            data,
            self.ASSOCIATED_DATA)
        return nonce.hex() + separator + cipher_text.hex()

    def decrypt(self, text: str, separator: str = ":") -> Optional[bytes]:
        try:
            (nonce, data) = text.split(separator, 1)
            result = self._cipher.decrypt(
                bytes.fromhex(nonce),
                bytes.fromhex(data),
                self.ASSOCIATED_DATA)
        except (ValueError, TypeError, InvalidTag):
            return None
        return result
