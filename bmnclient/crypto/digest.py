from __future__ import annotations

import hashlib
from abc import ABCMeta, abstractmethod
from typing import Final, Optional

from cryptography.hazmat.primitives.hashes import Hash, BLAKE2b, SHA256


class Digest(metaclass=ABCMeta):
    @abstractmethod
    def update(self, data: bytes) -> None:
        raise NotImplementedError

    @abstractmethod
    def final(self) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def copy(self) -> Digest:
        raise NotImplementedError


class Ripemd160Digest(Digest):
    SIZE: Final = 20

    def __init__(self, context: Optional[Digest] = None) -> None:
        self._context = context or hashlib.new("ripemd160")

    def update(self, data: bytes) -> None:
        self._context.update(data)

    def final(self) -> bytes:
        return self._context.digest()

    def copy(self) -> Ripemd160Digest:
        return Ripemd160Digest(self._context.copy())


class Sha256Digest(Digest):
    SIZE: Final = 32

    def __init__(self, context: Optional[Digest] = None) -> None:
        self._context = context or Hash(SHA256())

    def update(self, data: bytes) -> None:
        self._context.update(data)

    def final(self) -> bytes:
        return self._context.finalize()

    def copy(self) -> Sha256Digest:
        return Sha256Digest(self._context.copy())


class Blake2bDigest(Digest):
    SIZE: Final = 64

    def __init__(self, context: Optional[Digest] = None) -> None:
        self._context = context or Hash(BLAKE2b(64))

    def update(self, data: bytes) -> None:
        self._context.update(data)

    def final(self) -> bytes:
        return self._context.finalize()

    def copy(self) -> Blake2bDigest:
        return Blake2bDigest(self._context.copy())
