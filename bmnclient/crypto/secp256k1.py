# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from ecdsa.curves import SECP256k1
from ecdsa.keys import \
    BadDigestError, \
    BadSignatureError, \
    MalformedPointError, \
    SigningKey, \
    VerifyingKey
from ecdsa.util import sigdecode_der, sigencode_der_canonize

from .base58 import Base58
from .bech32 import Bech32
from .digest import HashlibWrapper, Ripemd160Digest, Sha256Digest
from ..utils.meta import classproperty

if TYPE_CHECKING:
    from typing import Final, Optional, Tuple, Union


def _hashHelper(data: Optional[bytes] = None):
    return HashlibWrapper(Sha256Digest(data))


class AbstractKey:
    _SIZE: int = 256 // 8
    _COMPRESSED_FLAG: int = 0x01
    _BYTE_ORDER: Final = "big"

    def __init__(
            self,
            key: Union[SigningKey, VerifyingKey],
            *,
            compressed: bool) -> None:
        self._key = key
        self._compressed = compressed
        self._data_cache: Optional[bytes] = None

    def __eq__(self, other: AbstractKey) -> bool:
        return (
                isinstance(other, self.__class__)
                and self._compressed == other._compressed
                and self.data == other.data
        )

    def __hash__(self) -> int:
        return hash((self._compressed, self.data))

    @classproperty
    def size(self) -> int:
        return self._SIZE

    @property
    def compressed(self) -> bool:
        return self._compressed

    def _data(self, *args) -> bytes:
        if self._data_cache is None:
            self._data_cache = self._key.to_string(*args)
            assert self._data_cache is not None
        return self._data_cache

    @property
    def data(self) -> bytes:
        raise NotImplementedError


class PublicKey(AbstractKey):
    @property
    def data(self) -> bytes:
        encoding = "compressed" if self._compressed else "uncompressed"
        return self._data(encoding)

    def verify(self, signature: bytes, data: bytes) -> bool:
        data = Sha256Digest(data).finalize()
        try:
            return self._key.verify_digest(
                signature,
                data,
                sigdecode_der)
        except (BadSignatureError, BadDigestError):
            return False

    def toBase58Address(self, version: int) -> Optional[str]:
        if not 0x00 <= version <= 0xff:
            return None
        version = version.to_bytes(1, self._BYTE_ORDER)
        data = Sha256Digest(self.data).finalize()
        data = Ripemd160Digest(data).finalize()
        return Base58.encode(version + data)

    def toBech32Address(self, hrp: str, version: int) -> Optional[str]:
        if not self._compressed:
            return None
        data = Sha256Digest(self.data).finalize()
        data = Ripemd160Digest(data).finalize()
        return Bech32.encode(hrp, version, data)


class PrivateKey(AbstractKey):
    def __init__(
            self,
            key: SigningKey,
            *,
            compressed: bool) -> None:
        super().__init__(key, compressed=compressed)
        self._public_key = PublicKey(
            self._key.verifying_key,
            compressed=self._compressed)

    @classmethod
    def fromSecretData(
            cls,
            secret_data: bytes,
            *,
            compressed: bool) -> Optional[PrivateKey]:
        return cls.fromSecretKey(
            int.from_bytes(secret_data, cls._BYTE_ORDER),
            compressed=compressed)

    @classmethod
    def fromSecretKey(
            cls,
            secret_key: int,
            *,
            compressed: bool) -> Optional[PrivateKey]:
        try:
            key = SigningKey.from_secret_exponent(
                secret_key,
                SECP256k1,
                _hashHelper)
        except (MalformedPointError, RuntimeError):
            return None

        return cls(key, compressed=compressed)

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
            compressed = True
        else:
            compressed = False

        if len(result) != cls.size:
            return 0, None

        result = cls.fromSecretKey(
            int.from_bytes(result, cls._BYTE_ORDER),
            compressed=compressed)
        if result is None:
            return 0, None

        return version, result

    def toWif(self, version: int) -> Optional[str]:
        if not 0x00 <= version <= 0xff:
            return None
        result = version.to_bytes(1, self._BYTE_ORDER) + self.data
        if self._compressed:
            result += self._COMPRESSED_FLAG.to_bytes(1, self._BYTE_ORDER)
        return Base58.encode(result)

    @property
    def data(self) -> bytes:
        return self._data()

    @property
    def publicKey(self) -> PublicKey:
        return self._public_key

    def sign(self, data: bytes) -> Optional[bytes]:
        data = Sha256Digest(data).finalize()
        return self._key.sign_digest_deterministic(
            data,
            None,
            sigencode_der_canonize)
