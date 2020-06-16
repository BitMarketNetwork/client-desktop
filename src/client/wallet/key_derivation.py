import os
import logging
import hashlib
# from cryptography.hazmat.primitives import hashes
# from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf import scrypt, pbkdf2
from cryptography.hazmat.primitives import hashes, hmac
from cryptography import exceptions
log = logging.getLogger(__name__)


class KeyDerivation:
    SALT_LEN = 16
    HASH_ALGO = hashes.BLAKE2b(64)
    """
    use Scrypt according to rfc7914 for verifying
    and PBKDF2 for hashing
    """

    def __init__(self, psw: str, length: int = 64, level: int = 18, value_length: int = 32):
        assert level >= 15  # the hole
        assert length >= 32
        sha = hashes.Hash(self.HASH_ALGO, default_backend())
        sha.update(psw.encode())
        self._hash = sha.finalize()
        self._len = length
        self._value_len = value_length
        self._level = level
        self._salt = None
        self._impl = None

    def _make_impl(self, salt: bytes):
        assert salt
        assert self._impl is None
        hm = hmac.HMAC(salt, self.HASH_ALGO, default_backend())
        hm.update(self._hash)
        salt_ = hm.finalize()
        self._impl = scrypt.Scrypt(
            salt=salt_,
            length=self._len,
            n=1 << self._level,
            r=8,  # recommended
            p=1,  # recommended
            backend=default_backend(),
        )
        return salt_

    def encode(self) -> bytes:
        salt = os.urandom(self.SALT_LEN)
        self._make_impl(salt)
        return salt + self._impl.derive(self._hash)

    def value(self) -> bytes:
        _value_impl = pbkdf2.PBKDF2HMAC(
            salt=self._salt,
            algorithm=self.HASH_ALGO,
            length=self._value_len,
            iterations=1 << self._level,
            backend=default_backend(),
        )
        return _value_impl.derive(self._hash)

    def check(self, ex: bytes) -> bool:
        try:
            assert len(ex) == self.SALT_LEN + self._len
            salt_, ex_ = ex[:self.SALT_LEN], ex[self.SALT_LEN:]
            self._salt = self._make_impl(salt_)
            self._impl.verify(key_material=self._hash, expected_key=ex_)
            return True
        except exceptions.AlreadyFinalized:
            log.critical(f"Already verified")
        except exceptions.InvalidKey:
            log.debug(f"Wrong key")
        except AssertionError:
            log.critical(f"ex:{len(ex)} len:{self._len}")
        return False
