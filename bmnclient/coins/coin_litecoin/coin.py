from __future__ import annotations

from ..coin_bitcoin import Bitcoin


class Litecoin(Bitcoin):
    _SHORT_NAME = "ltc"
    _FULL_NAME = "Litecoin"
    _BIP0044_COIN_TYPE = 2
    # https://github.com/litecoin-project/litecoin/blob/master/src/chainparams.cpp  # noqa
    _BIP0032_VERSION_PUBLIC_KEY = 0x0488B21E
    _BIP0032_VERSION_PRIVATE_KEY = 0x0488ADE4
    _WIF_VERSION = 0xB0

    class Currency(Bitcoin.Currency):
        _FULL_NAME = "LTC"
        _UNIT = "LTC"

    from .address import _Address

    Address = _Address
