# JOK4
from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from cryptography.hazmat.primitives import hashes, hmac

from ..utils.meta import classproperty

if TYPE_CHECKING:
    from typing import Any, Final, Optional, Tuple, Type


class AbstractDigest:
    _SIZE: int = 0

    def __init__(self, context) -> None:
        self._context = context

    @classproperty
    def size(cls) -> int:  # noqa
        return cls._SIZE

    def update(self, data: bytes) -> AbstractDigest:
        raise NotImplementedError

    def finalize(self) -> bytes:
        raise NotImplementedError

    def copy(self) -> AbstractDigest:
        raise NotImplementedError


class AbstractDigestHashlib(AbstractDigest):
    _HASHLIB_NAME: str = ""

    def __init__(self, context: Optional[object] = None) -> None:
        super().__init__(context or hashlib.new(self._HASHLIB_NAME))

    def update(self, data: bytes) -> AbstractDigestHashlib:
        self._context.update(data)
        return self

    def finalize(self) -> bytes:
        return self._context.digest()

    def copy(self) -> AbstractDigestHashlib:
        return self.__class__(self._context.copy())


class AbstractDigestHazmat(AbstractDigest):
    _HAZMAT_TYPE: Optional[Type[hashes.HashAlgorithm]] = None
    _HAZMAT_ARGS: Tuple[Any] = ()

    def __init__(self, context: Optional[hashes.HashAlgorithm] = None) -> None:
        if not context:
            # noinspection PyArgumentList
            context = hashes.Hash(self._HAZMAT_TYPE(*self._HAZMAT_ARGS))
        super().__init__(context)

    def update(self, data: bytes) -> AbstractDigestHazmat:
        self._context.update(data)
        return self

    def finalize(self) -> bytes:
        return self._context.finalize()

    def copy(self) -> AbstractDigestHazmat:
        return self.__class__(self._context.copy())


class Ripemd160Digest(AbstractDigestHashlib):
    _SIZE: Final = 160 // 8
    _HASHLIB_NAME: Final = "ripemd160"


class Sha256Digest(AbstractDigestHazmat):
    _SIZE: Final = 256 // 8
    _HAZMAT_TYPE: Final = hashes.SHA256


class Sha512Digest(AbstractDigestHazmat):
    _SIZE: Final = 512 // 8
    _HAZMAT_TYPE: Final = hashes.SHA512


class Blake2bDigest(AbstractDigestHazmat):
    _SIZE: Final = 512 // 8
    _HAZMAT_TYPE: Final = hashes.BLAKE2b
    _HAZMAT_ARGS: Final = (512 // 8, )


class Hmac(AbstractDigest):
    def __init__(
            self,
            key: Optional[bytes],
            digest: Optional[Type[AbstractDigestHazmat]],
            context: Optional[hmac.HMAC] = None) -> None:
        if not context:
            # noinspection PyArgumentList
            # noinspection PyProtectedMember
            context = hmac.HMAC(key, digest._HAZMAT_TYPE(*digest._HAZMAT_ARGS))
        super().__init__(context)

    def update(self, data: bytes) -> Hmac:
        self._context.update(data)
        return self

    def finalize(self) -> bytes:
        return self._context.finalize()

    def copy(self) -> AbstractDigest:
        return self.__class__(None, None, self._context.copy())

    def verify(self, signature: bytes) -> bool:
        return self._context.verify(signature)
