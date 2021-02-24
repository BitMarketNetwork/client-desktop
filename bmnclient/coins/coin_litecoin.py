# JOK++
from __future__ import annotations

from enum import Enum
from typing import Final

from .coin_bitcoin import Bitcoin, BitcoinAddress


class LitecoinAddress(BitcoinAddress):
    _PUBKEY_HASH_PREFIX_LIST = ("L",)
    _SCRIPT_HASH_PREFIX_LIST = ("M",)
    _HRP = "ltc"

    class Type(Enum):
        UNKNOWN: Final = \
            BitcoinAddress.Type.UNKNOWN.value
        PUBKEY_HASH: Final = \
            (0x30, ) + BitcoinAddress.Type.PUBKEY_HASH.value[1:]
        SCRIPT_HASH: Final = \
            (0x32, ) + BitcoinAddress.Type.SCRIPT_HASH.value[1:]
        WITNESS_V0_KEY_HASH: Final = \
            BitcoinAddress.Type.WITNESS_V0_KEY_HASH.value
        WITNESS_V0_SCRIPT_HASH: Final = \
            BitcoinAddress.Type.WITNESS_V0_SCRIPT_HASH.value
        WITNESS_UNKNOWN: Final = \
            BitcoinAddress.Type.WITNESS_UNKNOWN.value


class Litecoin(Bitcoin):
    _SHORT_NAME = "ltc"
    _FULL_NAME = "Litecoin"

    class _Currency(Bitcoin._Currency):
        _UNIT = "LTC"

    class _Address(LitecoinAddress):
        pass
