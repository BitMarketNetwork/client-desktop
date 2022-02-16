from __future__ import annotations

from typing import TYPE_CHECKING

from .script import _Script
from ..abstract import Coin
from ...crypto.base58 import Base58
from ...crypto.bech32 import Bech32
from ...crypto.digest import Hash160Digest, Sha256Digest

if TYPE_CHECKING:
    from typing import Final, Optional
    from . import Bitcoin


class _Address(Coin.Address):
    _PUBKEY_HASH_PREFIX_LIST = ("1",)
    _SCRIPT_HASH_PREFIX_LIST = ("3",)
    _HRP = "bc"

    class Type(Coin.Address.Type):
        UNKNOWN: Final = Coin.Address.TypeValue(
            name="unknown",
            version=0xff,
            size=0,
            encoding=None,
            is_witness=False,
            script_type=None,
            hd_purpose=None)
        PUBKEY_HASH: Final = Coin.Address.TypeValue(
            name="p2pkh",
            version=0x00,
            size=Hash160Digest.size,
            encoding=Coin.Address.Encoding.BASE58,
            is_witness=False,
            script_type=_Script.Type.P2PKH,
            hd_purpose=44)  # BIP-0044
        SCRIPT_HASH: Final = Coin.Address.TypeValue(
            name="p2sh",
            version=0x05,
            size=Hash160Digest.size,
            encoding=Coin.Address.Encoding.BASE58,
            is_witness=False,
            script_type=_Script.Type.P2SH,
            hd_purpose=None)
        WITNESS_V0_KEY_HASH: Final = Coin.Address.TypeValue(
            name="p2wpkh",
            version=0x00,
            size=Hash160Digest.size,
            encoding=Coin.Address.Encoding.BECH32,
            is_witness=True,
            script_type=_Script.Type.P2WPKH,
            hd_purpose=84)  # BIP-0084
        WITNESS_V0_SCRIPT_HASH: Final = Coin.Address.TypeValue(
            name="p2wsh",
            version=0x00,
            size=Sha256Digest.size,
            encoding=Coin.Address.Encoding.BECH32,
            is_witness=True,
            script_type=_Script.Type.P2WSH,
            hd_purpose=None)
        WITNESS_UNKNOWN: Final = Coin.Address.TypeValue(
            name="witness_unknown",
            version=0x00,
            size=-40,
            encoding=Coin.Address.Encoding.BECH32,
            is_witness=True,
            script_type=None,
            hd_purpose=None)
        DEFAULT = WITNESS_V0_KEY_HASH

    @classmethod
    def create(
            cls,
            coin: Bitcoin,
            *,
            type_: Bitcoin.Address.Type,
            key: Bitcoin.Address.KeyType,
            **kwargs) -> Optional[Bitcoin.Address]:
        public_key = cls._publicKey(key)
        if not public_key:
            return None
        if type_.value.encoding == cls.Encoding.BASE58:
            try:
                version = type_.value.version.to_bytes(1, "little")
            except OverflowError:
                return None
            name = Hash160Digest(public_key.data).finalize()
            name = Base58.encode(version + name)
        elif type_.value.encoding == cls.Encoding.BECH32:
            if not public_key.isCompressed:
                return None
            name = Hash160Digest(public_key.data).finalize()
            name = Bech32.encode(cls._HRP, type_.value.version, name)
        else:
            name = None

        if name is None:
            return None

        return coin.Address(
            coin,
            name=name,
            type_=type_,
            key=key,
            **kwargs)

    def _deriveHash(self) -> bytes:
        if self._type.value.encoding == self.Encoding.BASE58:
            data = Base58.decode(self._name)
            data = data[1:] if data is not None else None
        elif self._type.value.encoding == self.Encoding.BECH32:
            _,  _, data = Bech32.decode(self._name)
        else:
            data = None

        if data is None or not self._type.value.isValidSize(len(data)):
            return b""
        return data

    @classmethod
    def decode(
            cls,
            coin: Bitcoin,
            *,
            name: str,
            **kwargs) -> Optional[Bitcoin.Address]:
        if not name or len(name) <= len(cls._HRP) + 1:
            return None

        if name[0] in cls._PUBKEY_HASH_PREFIX_LIST:
            address_type = cls.Type.PUBKEY_HASH
        elif name[0] in cls._SCRIPT_HASH_PREFIX_LIST:
            address_type = cls.Type.SCRIPT_HASH

        elif name[len(cls._HRP)] != Bech32.separator:
            return None

        elif len(name) == len(cls._HRP) + 1 + 39:
            address_type = cls.Type.WITNESS_V0_KEY_HASH
        elif len(name) == len(cls._HRP) + 1 + 59:
            address_type = cls.Type.WITNESS_V0_SCRIPT_HASH

        else:
            address_type = cls.Type.WITNESS_UNKNOWN

        return cls._decode(coin, address_type, name=name, **kwargs)

    @classmethod
    def _decode(
            cls,
            coin: Bitcoin,
            address_type: Type,
            *,
            name: str,
            **kwargs) -> Optional[Bitcoin.Address]:
        if not address_type.value:
            return None

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

        if not address_type.value.isValidSize(len(data)):
            return None

        kwargs["type_"] = address_type
        return cls(coin, name=name, **kwargs)

    @classmethod
    def createNullData(cls, coin: Bitcoin, **kwargs) -> Bitcoin.Address:
        kwargs.setdefault("name", None)
        kwargs["type_"] = cls.Type.UNKNOWN
        return cls(coin, **kwargs)

    @property
    def isNullData(self) -> bool:
        return self._type == self.Type.UNKNOWN


class _TestAddress(_Address):
    _PUBKEY_HASH_PREFIX_LIST = ("m", "n")
    _SCRIPT_HASH_PREFIX_LIST = ("2",)
    _HRP = "tb"

    class Type(Coin.Address.Type):
        UNKNOWN: Final = \
            _Address.Type.UNKNOWN.value
        PUBKEY_HASH: Final = \
            _Address.Type.PUBKEY_HASH.value.copy(version=0x6f)
        SCRIPT_HASH: Final = \
            _Address.Type.SCRIPT_HASH.value.copy(version=0xc4)
        WITNESS_V0_KEY_HASH: Final = \
            _Address.Type.WITNESS_V0_KEY_HASH.value
        WITNESS_V0_SCRIPT_HASH: Final = \
            _Address.Type.WITNESS_V0_SCRIPT_HASH.value
        WITNESS_UNKNOWN: Final = \
            _Address.Type.WITNESS_UNKNOWN.value
        DEFAULT = WITNESS_V0_KEY_HASH
