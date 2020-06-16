import os
import logging
from typing import Union, Callable
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers import algorithms
from cryptography.hazmat.primitives.ciphers import modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import padding
from . import sym_encrypt_abc
from . import util
log = logging.getLogger(__name__)

"""
"""


class AesError(Exception):
    pass


class AesProvider(sym_encrypt_abc.SymEncryptAbc):
    HASHER = hashes.SHA256
    # PADDER = padding.ANSIX923
    AES_MODE = modes.CTR
    STRONG_LEN = 32
    WEAK_LEN = 16
    NONCE_LEN = 16

    def __init__(self, psw: Union[str, bytes], nonce: bytes):
        # split for future use
        self._weak_cipher = None
        self._psw = psw
        self._make_weak(psw, nonce)

    def _make_weak(self, psw, salt):
        self._weak_cipher = Cipher(
            algorithms.AES(self._prepare(psw, self.WEAK_LEN)),
            self.AES_MODE(self._prepare(salt, self.NONCE_LEN)),
            default_backend(),
        )

    def _make_strong(self, salt):
        return Cipher(
            algorithms.AES(self._prepare(self._psw, self.STRONG_LEN)),
            self.AES_MODE(self._prepare(salt, self.NONCE_LEN)),
            default_backend(),
        )

    def _prepare(self, psw: Union[str, bytes], size: int) -> bytes:
        digest = hashes.Hash(self.HASHER(), default_backend())
        digest.update(util.get_bytes(psw))
        return digest.finalize()[:size]

    def encode(self, data: bytes, strong: bool) -> bytes:
        if strong:
            nonce = os.urandom(16)
            cipher = self._make_strong(nonce)
        else:
            cipher = self._weak_cipher
        if not cipher:
            raise AesError("No cipher created. Set password at first.")
        enc = cipher.encryptor()
        if strong:
            return nonce + enc.update(util.get_bytes(data)) + enc.finalize()
        return enc.update(util.get_bytes(data)) + enc.finalize()

    def decode(self, data: bytes, strong: bool) -> bytes:
        if strong:
            nonce, data = data[:self.NONCE_LEN], data[self.NONCE_LEN:]
            cipher = self._make_strong(nonce,)
        else:
            cipher = self._weak_cipher
        if not cipher:
            raise AesError("No cipher created. Set password at first.")
        try:
            dec = cipher.decryptor()
            return dec.update(data) + dec.finalize()
        except ValueError as ve:
            raise AesError("Wrong password") from ve
