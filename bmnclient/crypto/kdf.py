# JOK+
import os
from typing import Optional

from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from .cipher import MessageCipher
from .digest import Blake2bDigest
from ..version import Product


class KeyDerivationFunction:
    HASH_ALGORITHM = Blake2bDigest
    KEY_COST = 18

    def __init__(self, password: str) -> None:
        password_hash = self.HASH_ALGORITHM()
        password_hash.update(
            Product.SHORT_NAME.encode(encoding=Product.ENCODING))
        password_hash.update(
            password.encode(encoding=Product.ENCODING))
        password_hash = password_hash.final()
        self._password_hash = password_hash

    def derive(
            self,
            salt: bytes,
            key_length: int) -> bytes:
        # https://stackoverflow.com/questions/11126315/what-are-optimal-scrypt-work-factors/30308723#30308723
        kdf = Scrypt(
            salt=salt,
            length=key_length,
            n=(1 << self.KEY_COST),
            r=8,  # RFC7914
            p=1   # RFC7914
        )
        return kdf.derive(self._password_hash)


class SecretStore(KeyDerivationFunction):
    SECRET_VERSION = "v1"
    SECRET_SALT_LENGTH = 128 // 8
    SECRET_KEY_LENGTH = 128 // 8

    def encryptValue(self, value: bytes) -> str:
        salt = os.urandom(self.SECRET_SALT_LENGTH)
        key = self.derive(salt, self.SECRET_KEY_LENGTH)
        result = self.SECRET_VERSION + Product.STRING_SEPARATOR
        result += salt.hex() + Product.STRING_SEPARATOR
        result += MessageCipher(key).encrypt(value, Product.STRING_SEPARATOR)
        return result

    def decryptValue(self, value: str) -> Optional[bytes]:
        try:
            (secret_version, salt, value) = value.split(
                Product.STRING_SEPARATOR,
                2)
        except ValueError:
            return None
        if secret_version != self.SECRET_VERSION:
            return None
        key = self.derive(bytes.fromhex(salt), self.SECRET_KEY_LENGTH)
        value = MessageCipher(key).decrypt(value, Product.STRING_SEPARATOR)
        return value
