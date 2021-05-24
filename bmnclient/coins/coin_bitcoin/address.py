# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from ..abstract.coin import AbstractCoin
from ...crypto.base58 import Base58
from ...crypto.bech32 import Bech32
from ...crypto.digest import Hash160Digest, Sha256Digest

if TYPE_CHECKING:
    from typing import Final, Optional
    from . import Bitcoin
    from ...crypto.secp256k1 import PublicKey


class _BitcoinAddress(AbstractCoin.Address):
    _PUBKEY_HASH_PREFIX_LIST = ("1",)
    _SCRIPT_HASH_PREFIX_LIST = ("3",)
    _HRP = "bc"

    class Type(AbstractCoin.Address.Type):
        UNKNOWN: Final = AbstractCoin.Address.TypeValue(
            name="unknown",
            version=0xff,
            size=0,
            encoding=AbstractCoin.Address.Encoding.NONE,
            is_segwit=False)
        PUBKEY_HASH: Final = AbstractCoin.Address.TypeValue(
            name="p2pkh",
            version=0x00,
            size=Hash160Digest.size,
            encoding=AbstractCoin.Address.Encoding.BASE58,
            is_segwit=False)
        SCRIPT_HASH: Final = AbstractCoin.Address.TypeValue(
            name="p2sh",
            version=0x05,
            size=Hash160Digest.size,
            encoding=AbstractCoin.Address.Encoding.BASE58,
            is_segwit=False)
        WITNESS_V0_KEY_HASH: Final = AbstractCoin.Address.TypeValue(
            name="p2wpkh",
            version=0x00,
            size=Hash160Digest.size,
            encoding=AbstractCoin.Address.Encoding.BECH32,
            is_segwit=True)
        WITNESS_V0_SCRIPT_HASH: Final = AbstractCoin.Address.TypeValue(
            name="p2wsh",
            version=0x00,
            size=Sha256Digest.size,
            encoding=AbstractCoin.Address.Encoding.BECH32,
            is_segwit=True)
        WITNESS_UNKNOWN: Final = AbstractCoin.Address.TypeValue(
            name="witness_unknown",
            version=0x00,
            size=-40,
            encoding=AbstractCoin.Address.Encoding.BECH32,
            is_segwit=True)
        DEFAULT = WITNESS_V0_KEY_HASH

    @classmethod
    def deriveAddressName(
            cls,
            type_: Bitcoin.Address.Type,
            public_key: PublicKey) -> Optional[str]:
        if type_.value.encoding == cls.Encoding.BASE58:
            try:
                version = type_.value.version.to_bytes(1, "big")
            except OverflowError:
                return None
            name = Hash160Digest(public_key.data).finalize()
            return Base58.encode(version + name)

        if type_.value.encoding == cls.Encoding.BECH32:
            if not public_key.isCompressed:
                return None
            name = Hash160Digest(public_key.data).finalize()
            return Bech32.encode(cls._HRP, type_.value.version, name)

        return None

    def _deriveHash(self) -> bytes:
        if self._type not in (
                self.Type.PUBKEY,
                self.Type.PUBKEY_HASH,
                self.Type.SCRIPT_HASH,
                self.Type.WITNESS_V0_KEY_HASH,
                self.Type.WITNESS_V0_SCRIPT_HASH):
            return b""

        if self._type.value.encoding == self.Encoding.BASE58:
            result = Base58.decode(self._name)
            result = result[1:] if result is not None else None
        elif self._type.value.encoding == self.Encoding.BECH32:
            _,  _, result = Bech32.decode(self._name)
        else:
            result = None

        if result is None or len(result) != self._type.value.size:
            return b""

        return result

    @classmethod
    def decode(
            cls,
            coin: Bitcoin,
            **kwargs) -> Optional[Bitcoin.Address]:
        name = kwargs.get("name")
        if not name or len(name) <= len(cls._HRP) + 1:
            return None

        if name[0] in cls._PUBKEY_HASH_PREFIX_LIST:
            return cls._decode(coin, cls.Type.PUBKEY_HASH, **kwargs)
        if name[0] in cls._SCRIPT_HASH_PREFIX_LIST:
            return cls._decode(coin, cls.Type.SCRIPT_HASH, **kwargs)

        if name[len(cls._HRP)] != Bech32.SEPARATOR:
            return None

        if len(name) == len(cls._HRP) + 1 + 39:
            return cls._decode(coin, cls.Type.WITNESS_V0_KEY_HASH, **kwargs)
        if len(name) == len(cls._HRP) + 1 + 59:
            return cls._decode(coin, cls.Type.WITNESS_V0_SCRIPT_HASH, **kwargs)

        return cls._decode(coin, cls.Type.WITNESS_UNKNOWN, **kwargs)

    @classmethod
    def _decode(
            cls,
            coin: Bitcoin,
            address_type: Type,
            **kwargs) -> Optional[Bitcoin.Address]:
        if not address_type.value:
            return None
        name = kwargs["name"]

        if address_type in (
                cls.Type.PUBKEY_HASH,
                cls.Type.SCRIPT_HASH
        ):
            data = Base58.decode(name, True)
            if not data or data[0] != address_type.value.version:
                return None
            data = data[1:]
        elif address_type in (
                cls.Type.WITNESS_V0_KEY_HASH,
                cls.Type.WITNESS_V0_SCRIPT_HASH
        ):
            name = name.lower()
            hrp, address_version, data = Bech32.decode(name)
            if hrp != cls._HRP or address_version != address_type.value.version:
                return None
        elif address_type == cls.Type.WITNESS_UNKNOWN:
            name = name.lower()
            hrp, address_version, data = Bech32.decode(name)
            if hrp != cls._HRP:
                return None
            for t in (
                    cls.Type.WITNESS_V0_KEY_HASH,
                    cls.Type.WITNESS_V0_SCRIPT_HASH
            ):
                if address_version == t.value.version:
                    return None
        else:
            return None

        if address_type.value.size > 0:
            if address_type.value.size != len(data):
                return None
        elif address_type.value.size < 0:
            if len(data) <= 0 or len(data) > abs(address_type.value.size):
                return None

        kwargs["name"] = name
        kwargs["type_"] = address_type
        return cls(coin, **kwargs)

    @classmethod
    def createNullData(cls, coin: Bitcoin, **kwargs) -> Bitcoin.Address:
        kwargs.setdefault("name", None)
        kwargs["type_"] = cls.Type.UNKNOWN
        return cls(coin, **kwargs)

    @property
    def isNullData(self) -> bool:
        return self._type == self.Type.UNKNOWN


class _BitcoinTestAddress(_BitcoinAddress):
    _PUBKEY_HASH_PREFIX_LIST = ("m", "n")
    _SCRIPT_HASH_PREFIX_LIST = ("2",)
    _HRP = "tb"

    class Type(AbstractCoin.Address.Type):
        UNKNOWN: Final = \
            _BitcoinAddress.Type.UNKNOWN.value
        PUBKEY_HASH: Final = \
            _BitcoinAddress.Type.PUBKEY_HASH.value.copy(version=0x6f)
        SCRIPT_HASH: Final = \
            _BitcoinAddress.Type.SCRIPT_HASH.value.copy(version=0xc4)
        WITNESS_V0_KEY_HASH: Final = \
            _BitcoinAddress.Type.WITNESS_V0_KEY_HASH.value
        WITNESS_V0_SCRIPT_HASH: Final = \
            _BitcoinAddress.Type.WITNESS_V0_SCRIPT_HASH.value
        WITNESS_UNKNOWN: Final = \
            _BitcoinAddress.Type.WITNESS_UNKNOWN.value
        DEFAULT = WITNESS_V0_KEY_HASH
