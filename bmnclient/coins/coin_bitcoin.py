# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from .abstract.coin import AbstractCoin
from ..crypto.base58 import Base58
from ..crypto.bech32 import Bech32
from ..crypto.digest import Hash160Digest, Sha256Digest

if TYPE_CHECKING:
    from typing import Final, Optional
    from ..crypto.secp256k1 import PublicKey


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


class _BitcoinScript(AbstractCoin.Script):
    class OpCode(AbstractCoin.Script.OpCode):
        OP_0: Final = 0x00
        OP_PUSHDATA1: Final = 0x4c
        OP_PUSHDATA2: Final = 0x4d
        OP_PUSHDATA4: Final = 0x4e
        OP_RETURN: Final = 0x6a
        OP_DUP: Final = 0x76
        OP_EQUAL: Final = 0x87
        OP_EQUALVERIFY: Final = 0x88
        OP_HASH160: Final = 0xa9
        OP_CHECKSIG: Final = 0xac

    @classmethod
    def addressToScript(
            cls,
            address: Bitcoin.Address,
            type_: Optional[Bitcoin.Address.Type] = None) -> Optional[bytes]:
        address_hash = address.hash
        if not (0 < len(address_hash) < 0xff):
            return None

        if type_ is None:
            type_ = address.type

        if type_ == address.Type.PUBKEY_HASH:
            if len(address_hash) != 0x14:
                return None
            script = (
                cls.OpCode.OP_DUP,
                cls.OpCode.OP_HASH160,
                len(address_hash),
                address_hash,
                cls.OpCode.OP_EQUALVERIFY,
                cls.OpCode.OP_CHECKSIG
            )
        elif type_ == address.Type.SCRIPT_HASH:
            if len(address_hash) != 0x14:
                return None
            script = (
                cls.OpCode.OP_HASH160,
                len(address_hash),
                address_hash,
                cls.OpCode.OP_EQUAL
            )
        elif type_ in (
                address.Type.WITNESS_V0_KEY_HASH,
                address.Type.WITNESS_V0_SCRIPT_HASH
        ):
            script = (
                cls.OpCode.OP_0,
                len(address_hash),
                address_hash
            )
        else:
            return None

        return cls.scriptToBytes(script)

    @classmethod
    def pushData(cls, data: bytes) -> Optional[bytes]:
        length = len(data)
        if length <= 0x4b:
            script = (
                cls.integerToBytes(length, 1),
                data)
        elif length <= 0xff:
            script = (
                cls.OpCode.OP_PUSHDATA1,
                cls.integerToBytes(length, 1),
                data)
        elif length <= 0xffff:
            script = (
                cls.OpCode.OP_PUSHDATA2,
                cls.integerToBytes(length, 2),
                data)
        elif length <= 0xffffffff:
            script = (
                cls.OpCode.OP_PUSHDATA4,
                cls.integerToBytes(length, 4),
                data)
        else:
            return None
        return cls.scriptToBytes(script)


class Bitcoin(AbstractCoin):
    _SHORT_NAME = "btc"
    _FULL_NAME = "Bitcoin"
    _BIP0044_COIN_TYPE = 0
    # https://github.com/bitcoin/bitcoin/blob/master/src/chainparams.cpp
    _BIP0032_VERSION_PUBLIC_KEY = 0x0488b21e
    _BIP0032_VERSION_PRIVATE_KEY = 0x0488ade4
    _WIF_VERSION = 0x80

    class Currency(AbstractCoin.Currency):
        _DECIMAL_SIZE = (0, 8)
        _UNIT = "BTC"

    Address = _BitcoinAddress
    Script = _BitcoinScript


################################################################################


class _BitcoinTestAddress(Bitcoin.Address):
    _PUBKEY_HASH_PREFIX_LIST = ("m", "n")
    _SCRIPT_HASH_PREFIX_LIST = ("2",)
    _HRP = "tb"

    class Type(AbstractCoin.Address.Type):
        UNKNOWN: Final = \
            Bitcoin.Address.Type.UNKNOWN.value
        PUBKEY_HASH: Final = \
            Bitcoin.Address.Type.PUBKEY_HASH.value.copy(version=0x6f)
        SCRIPT_HASH: Final = \
            Bitcoin.Address.Type.SCRIPT_HASH.value.copy(version=0xc4)
        WITNESS_V0_KEY_HASH: Final = \
            Bitcoin.Address.Type.WITNESS_V0_KEY_HASH.value
        WITNESS_V0_SCRIPT_HASH: Final = \
            Bitcoin.Address.Type.WITNESS_V0_SCRIPT_HASH.value
        WITNESS_UNKNOWN: Final = \
            Bitcoin.Address.Type.WITNESS_UNKNOWN.value
        DEFAULT = WITNESS_V0_KEY_HASH


class BitcoinTest(Bitcoin):
    _SHORT_NAME = "btctest"
    _FULL_NAME = "Bitcoin Testnet"
    _IS_TEST_NET = True
    _BIP0044_COIN_TYPE = 1
    _BIP0032_VERSION_PUBLIC_KEY = 0x043587cf
    _BIP0032_VERSION_PRIVATE_KEY = 0x04358394
    _WIF_VERSION = 0xef

    Address = _BitcoinTestAddress
