# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from ecdsa.curves import SECP256k1
from ecdsa.ellipticcurve import INFINITY, Point
from ecdsa.keys import \
    BadDigestError, \
    BadSignatureError, \
    MalformedPointError, \
    SigningKey, \
    VerifyingKey
from ecdsa.util import sigdecode_der, sigencode_der_canonize

from .base58 import Base58
from .digest import HashlibWrapper, Sha256Digest
from ..utils import NotImplementedInstance
from ..utils.class_property import classproperty
from ..utils.integer import BigOrderIntegerConverter

if TYPE_CHECKING:
    from typing import Final, Optional, Tuple, Union

_CURVE: Final = SECP256k1


def _hashHelper(data: Optional[bytes] = None):
    return HashlibWrapper(Sha256Digest(data))


class KeyUtils(NotImplementedInstance, BigOrderIntegerConverter):
    @classproperty
    def n(cls) -> int:  # noqa
        return _CURVE.order


class AbstractKey:
    _SIZE: int = 256 // 8
    _COMPRESSED_FLAG: int = 0x01

    def __init__(
            self,
            key: Union[SigningKey, VerifyingKey],
            *,
            is_compressed: bool) -> None:
        self._key = key
        self._is_compressed = is_compressed
        self._data_cache: Optional[bytes] = None

    def __eq__(self, other: AbstractKey) -> bool:
        return (
                isinstance(other, self.__class__)
                and self._is_compressed == other._is_compressed
                and self.data == other.data
        )

    def __hash__(self) -> int:
        return hash((self._is_compressed, self.data))

    @classproperty
    def size(cls) -> int:  # noqa
        return cls._SIZE

    @property
    def isCompressed(self) -> bool:
        return self._is_compressed

    def _data(self, *args) -> bytes:
        if self._data_cache is None:
            self._data_cache = self._key.to_string(*args)
            assert self._data_cache is not None
        return self._data_cache

    @property
    def data(self) -> bytes:
        raise NotImplementedError


class PublicKey(AbstractKey):
    @classproperty
    def compressedSize(cls) -> int:  # noqa
        return cls._SIZE + 1

    @classproperty
    def uncompressedSize(cls) -> int:  # noqa
        return cls._SIZE * 2 + 1

    @classmethod
    def fromPublicData(cls, data: bytes) -> Optional[PublicKey]:
        try:
            key = VerifyingKey.from_string(
                data,
                _CURVE,
                _hashHelper,
                True)
        except (MalformedPointError, RuntimeError):
            return None

        return cls(
            key,
            is_compressed=(len(data) == _CURVE.baselen + 1))

    @classmethod
    def fromPublicInteger(
            cls,
            integer: int,
            parent_point: Optional[Tuple[int, int]],
            *,
            is_compressed: bool) -> Optional[PublicKey]:
        if integer >= KeyUtils.n:
            return None

        try:
            point = integer * _CURVE.generator
            if parent_point is not None:
                point += Point(
                    _CURVE.curve,
                    parent_point[0],
                    parent_point[1],
                    _CURVE.order)
            if point == INFINITY:
                return None

            key = VerifyingKey.from_public_point(
                point,
                _CURVE,
                _hashHelper,
                True)
        except (MalformedPointError, RuntimeError):
            return None

        return cls(key, is_compressed=is_compressed)

    @property
    def data(self) -> bytes:
        encoding = "compressed" if self._is_compressed else "uncompressed"
        return self._data(encoding)

    @property
    def point(self) -> Tuple[int, int]:
        return self._key.pubkey.point.x(), self._key.pubkey.point.y()

    def verify(self, signature: bytes, data: bytes) -> bool:
        data = Sha256Digest(data).finalize()
        try:
            return self._key.verify_digest(
                signature,
                data,
                sigdecode_der)
        except (BadSignatureError, BadDigestError):
            return False


class PrivateKey(AbstractKey):
    _SIGNATURE_MAX_SIZE = 1 + 70  # DER

    def __init__(
            self,
            key: SigningKey,
            *,
            is_compressed: bool) -> None:
        super().__init__(key, is_compressed=is_compressed)
        self._public_key = PublicKey(
            self._key.verifying_key,
            is_compressed=self._is_compressed)

    @classmethod
    def fromSecretData(
            cls,
            secret_data: bytes,
            *,
            is_compressed: bool) -> Optional[PrivateKey]:
        return cls.fromSecretInteger(
            KeyUtils.integerFromBytes(secret_data),
            is_compressed=is_compressed)

    @classmethod
    def fromSecretInteger(
            cls,
            integer: int,
            *,
            is_compressed: bool) -> Optional[PrivateKey]:
        if not 0 < integer < KeyUtils.n:
            return None

        try:
            key = SigningKey.from_secret_exponent(
                integer,
                _CURVE,
                _hashHelper)
        except (MalformedPointError, RuntimeError):
            return None

        return cls(key, is_compressed=is_compressed)

    @classmethod
    def fromWif(cls, wif_string: str) -> Tuple[int, Optional[PrivateKey]]:
        # https://en.bitcoin.it/wiki/Wallet_import_format
        result = Base58.decode(wif_string)
        if result is None or len(result) < cls.size + 1:
            return 0, None
        version = int(result[0])
        result = result[1:]

        if len(result) == cls.size + 1:
            if result[-1] != cls._COMPRESSED_FLAG:
                return 0, None
            result = result[:-1]
            is_compressed = True
        else:
            is_compressed = False

        if len(result) != cls.size:
            return 0, None

        result = cls.fromSecretInteger(
            KeyUtils.integerFromBytes(result),
            is_compressed=is_compressed)
        if result is None:
            return 0, None

        return version, result

    def toWif(self, version: int) -> Optional[str]:
        result = KeyUtils.integerToBytes(version, 1)
        if result is None:
            return None
        result += self.data
        if self._is_compressed:
            result += KeyUtils.integerToBytes(self._COMPRESSED_FLAG, 1)
        return Base58.encode(result)

    @property
    def data(self) -> bytes:
        return self._data()

    @property
    def publicKey(self) -> PublicKey:
        return self._public_key

    @classproperty
    def signatureMaxSize(cls) -> int:  # noqa
        return cls._SIGNATURE_MAX_SIZE

    def sign(self, data: bytes) -> Optional[bytes]:
        data = Sha256Digest(data).finalize()
        return self._key.sign_digest_deterministic(
            data,
            None,
            sigencode_der_canonize)
