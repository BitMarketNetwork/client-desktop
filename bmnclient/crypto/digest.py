from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from cryptography.hazmat.primitives import hashes, hmac

from ..utils.class_property import classproperty

if TYPE_CHECKING:
    from typing import Any, Final, Optional, Tuple, Type


class AbstractDigest:
    _NAME: str = ""
    _SIZE: int = 0
    _BLOCK_SIZE: int = 0

    def __init__(
            self,
            data: Optional[bytes] = None,
            *,
            context: Any) -> None:
        self._context = context
        if data is not None:
            self.update(data)

    @classproperty
    def name(cls) -> str:  # noqa
        return cls._NAME

    @classproperty
    def size(cls) -> int:  # noqa
        return cls._SIZE

    @classproperty
    def blockSize(cls) -> int:  # noqa
        return cls._BLOCK_SIZE

    def update(self, data: bytes) -> AbstractDigest:
        raise NotImplementedError

    def finalize(self) -> bytes:
        raise NotImplementedError

    def copy(self) -> AbstractDigest:
        raise NotImplementedError


class AbstractDigestHashlib(AbstractDigest):
    _HASHLIB_NAME: str = ""

    def __init__(
            self,
            data: Optional[bytes] = None,
            *,
            context: Optional[object] = None) -> None:
        super().__init__(
            data,
            context=context or hashlib.new(self._HASHLIB_NAME))

    def update(self, data: bytes) -> AbstractDigestHashlib:
        self._context.update(data)
        return self

    def finalize(self) -> bytes:
        return self._context.digest()

    def copy(self) -> AbstractDigestHashlib:
        return self.__class__(context=self._context.copy())


class AbstractDigestHazmat(AbstractDigest):
    _HAZMAT_TYPE: Optional[Type[hashes.HashAlgorithm]] = None
    _HAZMAT_ARGS: Tuple[Any] = ()

    def __init__(
            self,
            data: Optional[bytes] = None,
            *,
            context: Optional[hashes.HashAlgorithm] = None) -> None:
        if not context:
            # noinspection PyArgumentList
            context = hashes.Hash(self._HAZMAT_TYPE(*self._HAZMAT_ARGS))
        super().__init__(data, context=context)

    def update(self, data: bytes) -> AbstractDigestHazmat:
        self._context.update(data)
        return self

    def finalize(self) -> bytes:
        return self._context.finalize()

    def copy(self) -> AbstractDigestHazmat:
        return self.__class__(context=self._context.copy())


class HashlibWrapper:
    def __init__(self, digest: AbstractDigest) -> None:
        self._digest = digest

    @property
    def name(self) -> str:
        return self._digest.name

    @property
    def digest_size(self) -> int:
        return self._digest.size

    @property
    def block_size(self) -> int:
        return self._digest.blockSize

    def update(self, data: bytes) -> None:
        self._digest.update(data)

    def digest(self) -> bytes:
        return self._digest.finalize()

    def hexdigest(self) -> str:
        return self.digest().hex()

    def copy(self) -> HashlibWrapper:
        return self.__class__(self._digest.copy())


class Ripemd160Digest(AbstractDigestHashlib):
    _NAME: Final = "ripemd160"
    _SIZE: Final = 160 // 8
    _BLOCK_SIZE: Final = 64
    _HASHLIB_NAME: Final = "ripemd160"


class Sha256Digest(AbstractDigestHazmat):
    _NAME = "sha256"
    _SIZE: Final = 256 // 8
    _BLOCK_SIZE: Final = 64
    _HAZMAT_TYPE: Final = hashes.SHA256


class Sha256DoubleDigest(Sha256Digest):
    _NAME: Final = "sha256d"

    def finalize(self) -> bytes:
        return Sha256Digest(super().finalize()).finalize()


class Sha512Digest(AbstractDigestHazmat):
    _NAME: Final = "sha512"
    _SIZE: Final = 512 // 8
    _BLOCK_SIZE: Final = 128
    _HAZMAT_TYPE: Final = hashes.SHA512


class Blake2bDigest(AbstractDigestHazmat):
    _NAME: Final = "blake2b"
    _SIZE: Final = 512 // 8
    _BLOCK_SIZE: Final = 128
    _HAZMAT_TYPE: Final = hashes.BLAKE2b
    _HAZMAT_ARGS: Final = (512 // 8, )


# Ripemd160Digest after Sha256Digest
class Hash160Digest(AbstractDigest):
    _NAME: Final = "hash160"
    _SIZE = Ripemd160Digest.size
    _BLOCK_SIZE = Ripemd160Digest.blockSize

    def __init__(
            self,
            data: Optional[bytes] = None,
            *,
            context: Optional[Sha256Digest] = None) -> None:
        super().__init__(
            data,
            context=context or Sha256Digest())

    def update(self, data: bytes) -> AbstractDigest:
        return self._context.update(data)

    def finalize(self) -> bytes:
        return Ripemd160Digest(self._context.finalize()).finalize()

    def copy(self) -> AbstractDigest:
        return self.__class__(context=self._context.copy())


class Hmac(AbstractDigest):
    def __init__(
            self,
            key: Optional[bytes],
            digest: Optional[Type[AbstractDigestHazmat]],
            data: Optional[bytes] = None,
            *,
            context: Optional[hmac.HMAC] = None) -> None:
        if not context:
            # noinspection PyArgumentList
            # noinspection PyProtectedMember
            context = hmac.HMAC(key, digest._HAZMAT_TYPE(*digest._HAZMAT_ARGS))
        super().__init__(data, context=context)

    def update(self, data: bytes) -> Hmac:
        self._context.update(data)
        return self

    def finalize(self) -> bytes:
        return self._context.finalize()

    def copy(self) -> AbstractDigest:
        return self.__class__(None, None, context=self._context.copy())

    def verify(self, signature: bytes) -> bool:
        return self._context.verify(signature)
