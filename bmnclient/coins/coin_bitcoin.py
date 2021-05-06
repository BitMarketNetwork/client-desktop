# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from .abstract.coin import AbstractCoin
from ..crypto.base58 import Base58
from ..crypto.bech32 import Bech32
from ..crypto.digest import Ripemd160Digest, Sha256Digest

if TYPE_CHECKING:
    from typing import Final, Optional


class BitcoinAddress(AbstractCoin.Address):
    _PUBKEY_HASH_PREFIX_LIST = ("1",)
    _SCRIPT_HASH_PREFIX_LIST = ("3",)
    _HRP = "bc"

    class Type(AbstractCoin.Address.Type):
        UNKNOWN: Final = AbstractCoin.Address.TypeValue(
            name="unknown",
            version=0xff,
            size=0)
        PUBKEY_HASH: Final = AbstractCoin.Address.TypeValue(
            name="p2pkh",
            version=0x00,
            size=Ripemd160Digest.SIZE)
        SCRIPT_HASH: Final = AbstractCoin.Address.TypeValue(
            name="p2sh",
            version=0x05,
            size=Ripemd160Digest.SIZE)
        WITNESS_V0_KEY_HASH: Final = AbstractCoin.Address.TypeValue(
            name="p2wpkh",
            version=0x00,
            size=Ripemd160Digest.SIZE)
        WITNESS_V0_SCRIPT_HASH: Final = AbstractCoin.Address.TypeValue(
            name="p2wsh",
            version=0x00,
            size=Sha256Digest.SIZE)
        WITNESS_UNKNOWN: Final = AbstractCoin.Address.TypeValue(
            name="witness_unknown",
            version=0x00,
            size=-40)
        DEFAULT = WITNESS_V0_KEY_HASH

    @classmethod
    def decode(
            cls,
            coin: Bitcoin,
            **kwargs) -> Optional[BitcoinAddress]:
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
            **kwargs) -> Optional[BitcoinAddress]:
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
        kwargs["data"] = data
        return cls(coin, **kwargs)

    @classmethod
    def createNullData(cls, coin: AbstractCoin, **kwargs) -> BitcoinAddress:
        kwargs.setdefault("name", None)
        kwargs["type_"] = cls.Type.UNKNOWN
        return cls(coin, **kwargs)

    @property
    def isNullData(self) -> bool:
        return self._type == self.Type.UNKNOWN


class Bitcoin(AbstractCoin):
    _SHORT_NAME = "btc"
    _FULL_NAME = "Bitcoin"
    _BIP0044_COIN_TYPE = 0

    class Currency(AbstractCoin.Currency):
        _DECIMAL_SIZE = (0, 8)
        _UNIT = "BTC"

    class Address(BitcoinAddress):
        pass


class BitcoinTestAddress(BitcoinAddress):
    _PUBKEY_HASH_PREFIX_LIST = ("m", "n")
    _SCRIPT_HASH_PREFIX_LIST = ("2",)
    _HRP = "tb"

    class Type(AbstractCoin.Address.Type):
        UNKNOWN: Final = \
            BitcoinAddress.Type.UNKNOWN.value
        PUBKEY_HASH: Final = AbstractCoin.Address.TypeValue(
            name=BitcoinAddress.Type.PUBKEY_HASH.value.name,
            version=0x6f,
            size=BitcoinAddress.Type.PUBKEY_HASH.value.size)
        SCRIPT_HASH: Final = AbstractCoin.Address.TypeValue(
            name=BitcoinAddress.Type.SCRIPT_HASH.value.name,
            version=0xc4,
            size=BitcoinAddress.Type.SCRIPT_HASH.value.size)
        WITNESS_V0_KEY_HASH: Final = \
            BitcoinAddress.Type.WITNESS_V0_KEY_HASH.value
        WITNESS_V0_SCRIPT_HASH: Final = \
            BitcoinAddress.Type.WITNESS_V0_SCRIPT_HASH.value
        WITNESS_UNKNOWN: Final = \
            BitcoinAddress.Type.WITNESS_UNKNOWN.value
        DEFAULT = WITNESS_V0_KEY_HASH


class BitcoinTest(Bitcoin):
    _SHORT_NAME = "btctest"
    _FULL_NAME = "Bitcoin Testnet"
    _IS_TEST_NET = True
    _BIP0044_COIN_TYPE = 1

    class Address(BitcoinTestAddress):
        pass
