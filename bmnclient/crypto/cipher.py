# JOK+
import os
from typing import Optional

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers import aead

from ..version import Product


class AeadCipher:
    CIPHER = aead.AESGCM
    NONCE_LENGTH = 96 // 8  # NIST recommends
    KEY_LENGTH = 128 // 8
    ASSOCIATED_DATA = Product.SHORT_NAME.encode(encoding=Product.ENCODING)

    def __init__(self, key: bytes, nonce: Optional[bytes] = None) -> None:
        self._cipher = self.CIPHER(key)
        self._nonce = nonce

    @classmethod
    def generateNonce(cls) -> bytes:
        return os.urandom(cls.NONCE_LENGTH)

    @classmethod
    def generateKey(cls) -> bytes:
        return cls.CIPHER.generate_key(cls.KEY_LENGTH * 8)

    def encrypt(self, nonce: Optional[bytes], data: bytes) -> bytes:
        return self._cipher.encrypt(
            nonce or self._nonce,
            data,
            self.ASSOCIATED_DATA)

    def decrypt(self, nonce: Optional[bytes], data: bytes) -> Optional[bytes]:
        try:
            return self._cipher.decrypt(
                nonce or self._nonce,
                data,
                self.ASSOCIATED_DATA)
        except InvalidTag:
            return None


class MessageCipher(AeadCipher):
    def __init(self, key: bytes):
        super().__init__(key, None)

    def encrypt(
            self,
            data: bytes,
            separator: str = Product.STRING_SEPARATOR) -> str:
        nonce = self.generateNonce()
        cipher_text = super().encrypt(nonce, data)
        return nonce.hex() + separator + cipher_text.hex()

    def decrypt(
            self,
            text: str,
            separator: str = Product.STRING_SEPARATOR) -> Optional[bytes]:
        try:
            (nonce, data) = text.split(separator, 1)
            return super().decrypt(
                bytes.fromhex(nonce),
                bytes.fromhex(data))
        except (ValueError, TypeError):
            return None


class StreamCipher:
    pass
