# JOK4
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from .cipher import MessageCipher
from .digest import Blake2bDigest
from ..version import Product

if TYPE_CHECKING:
    from typing import Final, Optional


class KeyDerivationFunction:
    _HASH_ALGORITHM: Final = Blake2bDigest
    _KEY_COST: Final = 18

    def __init__(self, password: str) -> None:
        password_hash = self._HASH_ALGORITHM()
        password_hash.update(Product.SHORT_NAME.encode(Product.ENCODING))
        password_hash.update(password.encode(Product.ENCODING))
        password_hash = password_hash.finalize()
        self._password_hash = password_hash

    def derive(
            self,
            salt: bytes,
            key_length: int) -> bytes:
        # https://stackoverflow.com/questions/11126315/what-are-optimal-scrypt-work-factors/30308723#30308723
        kdf = Scrypt(
            salt=salt,
            length=key_length,
            n=(1 << self._KEY_COST),
            r=8,  # RFC7914
            p=1   # RFC7914
        )
        return kdf.derive(self._password_hash)


class SecretStore(KeyDerivationFunction):
    _SECRET_VERSION: Final = "v1"
    _SECRET_SALT_LENGTH: Final = 128 // 8
    _SECRET_KEY_LENGTH: Final = 128 // 8

    def encryptValue(self, value: bytes) -> str:
        salt = os.urandom(self._SECRET_SALT_LENGTH)
        key = self.derive(salt, self._SECRET_KEY_LENGTH)
        result = self._SECRET_VERSION + Product.STRING_SEPARATOR
        result += salt.hex() + Product.STRING_SEPARATOR
        result += MessageCipher(key).encrypt(value, Product.STRING_SEPARATOR)
        return result

    def decryptValue(self, value: str) -> Optional[bytes]:
        try:
            (secret_version, salt, value) = value.split(
                Product.STRING_SEPARATOR,
                2)
            salt = bytes.fromhex(salt)
        except ValueError:
            return None
        if secret_version != self._SECRET_VERSION:
            return None
        key = self.derive(salt, self._SECRET_KEY_LENGTH)
        value = MessageCipher(key).decrypt(value, Product.STRING_SEPARATOR)
        return value
