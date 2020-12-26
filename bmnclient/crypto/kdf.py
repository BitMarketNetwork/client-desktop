# JOK+
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from bmnclient import version
from .cipher import MessageCipher


class KeyDerivationFunction:
    ENCODING = version.PYTHON_ENCODING
    HASH_ALGORITHM = hashes.BLAKE2b(64)
    HASH_SALT = b"passphrase1"

    KEY_COST = 18

    SECRET_SEPARATOR = ":"
    SECRET_VERSION = "v1"
    SECRET_VALUE = version.SHORT_NAME.encode(encoding=ENCODING)
    SECRET_KEY_LENGTH = 128 // 8
    SECRET_SALT = b"secret1"

    def __init__(self) -> None:
        self._passphrase_hash = None

    def setPassphrase(self, passphrase: str) -> None:
        passphrase_hash = hashes.Hash(self.HASH_ALGORITHM)
        passphrase_hash.update(
            version.SHORT_NAME.encode(encoding=self.ENCODING))
        passphrase_hash.update(
            passphrase.encode(encoding=self.ENCODING))
        passphrase_hash.update(
            self.HASH_SALT)
        passphrase_hash = passphrase_hash.finalize()
        self._passphrase_hash = passphrase_hash

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
        return kdf.derive(self._passphrase_hash)

    def verifySecret(self, secret: str) -> bool:
        key = self.derive(self.SECRET_SALT, self.SECRET_KEY_LENGTH)

        (secret_version, secret) = secret.split(self.SECRET_SEPARATOR, 1)
        if secret_version != self.SECRET_VERSION:
            return False
        result = MessageCipher(key).decrypt(secret, self.SECRET_SEPARATOR)
        return result == self.SECRET_VALUE

    def createSecret(self) -> str:
        key = self.derive(self.SECRET_SALT, self.SECRET_KEY_LENGTH)
        secret = self.SECRET_VERSION + self.SECRET_SEPARATOR
        secret += MessageCipher(key).encrypt(
            self.SECRET_VALUE,
            self.SECRET_SEPARATOR)
        return secret
