import os
import logging
from typing import Union, Callable, Optional
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers import algorithms
from cryptography.hazmat.primitives.ciphers import modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from . import sym_encrypt_abc
from . import util
log = logging.getLogger(__name__)


class AesError(Exception):
    pass


class AesProvider(sym_encrypt_abc.SymEncryptAbc):
    HASHER = hashes.SHA256
    AES_MODE = modes.CTR
    STRONG_LEN = 32
    WEAK_LEN = 16
    NONCE_LEN = 16

    def __init__(self, psw: Union[str, bytes], weak_nonce: Optional[bytes] = None):
        # split for future use
        self.__weak_cipher = None
        self.__psw = psw
        if weak_nonce is not None:
            self.__weak_cipher = Cipher(
                algorithms.AES(self.__prepare(psw, self.WEAK_LEN)),
                self.AES_MODE(self.__prepare(weak_nonce, self.NONCE_LEN)))

    def __make_strong(self, salt):
        return Cipher(
            algorithms.AES(self.__prepare(self.__psw, self.STRONG_LEN)),
            self.AES_MODE(self.__prepare(salt, self.NONCE_LEN)))

    def __prepare(self, psw: Union[str, bytes], size: int) -> bytes:
        digest = hashes.Hash(self.HASHER(), default_backend())
        digest.update(util.get_bytes(psw))
        return digest.finalize()[:size]

    def encode(self, data: bytes, strong: bool) -> bytes:
        if strong:
            nonce = os.urandom(16)
            cipher = self.__make_strong(nonce)
        else:
            cipher = self.__weak_cipher
        if not cipher:
            raise AesError("No cipher created. Set password at first.")
        enc = cipher.encryptor()
        if strong:
            return nonce + enc.update(util.get_bytes(data)) + enc.finalize()
        return enc.update(util.get_bytes(data)) + enc.finalize()

    def decode(self, data: bytes, strong: bool) -> bytes:
        if strong:
            nonce, data = data[:self.NONCE_LEN], data[self.NONCE_LEN:]
            cipher = self.__make_strong(nonce,)
        else:
            cipher = self.__weak_cipher
        if not cipher:
            raise AesError("No cipher created. Set password at first.")
        try:
            dec = cipher.decryptor()
            return dec.update(data) + dec.finalize()
        except ValueError as ve:
            raise AesError("Wrong password") from ve
