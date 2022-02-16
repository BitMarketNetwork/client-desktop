from __future__ import annotations

from .address import _Address
from ..coin_bitcoin import Bitcoin


class _Currency(Bitcoin.Currency):
    _FULL_NAME = "LTC"
    _UNIT = "LTC"


class Litecoin(Bitcoin):
    _SHORT_NAME = "ltc"
    _FULL_NAME = "Litecoin"
    _BIP0044_COIN_TYPE = 2
    # https://github.com/litecoin-project/litecoin/blob/master/src/chainparams.cpp
    _BIP0032_VERSION_PUBLIC_KEY = 0x0488b21e
    _BIP0032_VERSION_PRIVATE_KEY = 0x0488ade4
    _WIF_VERSION = 0xb0

    Currency = _Currency
    Address = _Address
