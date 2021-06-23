from __future__ import annotations

import os
from typing import TYPE_CHECKING

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers import aead

from ..version import Product

if TYPE_CHECKING:
    from typing import Final, Optional


class AeadCipher:
    _CIPHER: Final = aead.AESGCM
    _NONCE_LENGTH: Final = 96 // 8  # NIST recommends
    _KEY_LENGTH: Final = 128 // 8
    _ASSOCIATED_DATA: Final = Product.SHORT_NAME.encode(Product.ENCODING)

    def __init__(self, key: bytes, nonce: Optional[bytes] = None) -> None:
        self._cipher = self._CIPHER(key)
        self._nonce = nonce

    @classmethod
    def generateNonce(cls) -> bytes:
        return os.urandom(cls._NONCE_LENGTH)

    @classmethod
    def generateKey(cls) -> bytes:
        return cls._CIPHER.generate_key(cls._KEY_LENGTH * 8)

    def encrypt(self, nonce: Optional[bytes], data: bytes) -> bytes:
        return self._cipher.encrypt(
            nonce or self._nonce,
            data,
            self._ASSOCIATED_DATA)

    def decrypt(self, nonce: Optional[bytes], data: bytes) -> Optional[bytes]:
        try:
            return self._cipher.decrypt(
                nonce or self._nonce,
                data,
                self._ASSOCIATED_DATA)
        except InvalidTag:
            return None


class MessageCipher(AeadCipher):
    def __init(self, key: bytes) -> None:
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
