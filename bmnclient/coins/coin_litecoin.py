# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from .coin_bitcoin import AbstractCoin, Bitcoin, BitcoinAddress

if TYPE_CHECKING:
    from typing import Final


class LitecoinAddress(BitcoinAddress):
    _PUBKEY_HASH_PREFIX_LIST = ("L",)
    _SCRIPT_HASH_PREFIX_LIST = ("M",)
    _HRP = "ltc"

    class Type(AbstractCoin.Address.Type):
        UNKNOWN: Final = \
            BitcoinAddress.Type.UNKNOWN.value
        PUBKEY_HASH: Final = AbstractCoin.Address.TypeValue(
            name=BitcoinAddress.Type.PUBKEY_HASH.value.name,
            version=0x30,
            size=BitcoinAddress.Type.PUBKEY_HASH.value.size,
            encoding=BitcoinAddress.Type.PUBKEY_HASH.value.encoding)
        SCRIPT_HASH: Final = AbstractCoin.Address.TypeValue(
            name=BitcoinAddress.Type.SCRIPT_HASH.value.name,
            version=0x32,
            size=BitcoinAddress.Type.SCRIPT_HASH.value.size,
            encoding=BitcoinAddress.Type.SCRIPT_HASH.value.encoding)
        WITNESS_V0_KEY_HASH: Final = \
            BitcoinAddress.Type.WITNESS_V0_KEY_HASH.value
        WITNESS_V0_SCRIPT_HASH: Final = \
            BitcoinAddress.Type.WITNESS_V0_SCRIPT_HASH.value
        WITNESS_UNKNOWN: Final = \
            BitcoinAddress.Type.WITNESS_UNKNOWN.value
        DEFAULT = WITNESS_V0_KEY_HASH


class Litecoin(Bitcoin):
    _SHORT_NAME = "ltc"
    _FULL_NAME = "Litecoin"
    _BIP0044_COIN_TYPE = 2
    # https://github.com/litecoin-project/litecoin/blob/master/src/chainparams.cpp
    _BIP0032_VERSION_PUBLIC_KEY = 0x0488b21e
    _BIP0032_VERSION_PRIVATE_KEY = 0x0488ade4
    _WIF_VERSION = 0xb0

    class Currency(Bitcoin.Currency):
        _UNIT = "LTC"

    class Address(LitecoinAddress):
        pass
