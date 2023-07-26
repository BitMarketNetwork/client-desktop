from __future__ import annotations

from ..abstract import Coin


class Bitcoin(Coin):
    _SHORT_NAME = "btc"
    _FULL_NAME = "Bitcoin"
    _BIP0044_COIN_TYPE = 0
    # https://github.com/bitcoin/bitcoin/blob/master/src/chainparams.cpp
    _BIP0032_VERSION_PUBLIC_KEY = 0x0488B21E
    _BIP0032_VERSION_PRIVATE_KEY = 0x0488ADE4
    _WIF_VERSION = 0x80

    class Currency(Coin.Currency):
        _DECIMAL_SIZE = (0, 8)
        _FULL_NAME = "BTC"
        _UNIT = "BTC"

    from .address import _Address

    Address = _Address

    from .tx_factory import _TxFactory

    TxFactory = _TxFactory


class BitcoinTest(Bitcoin):
    _SHORT_NAME = "btctest"
    _FULL_NAME = "Bitcoin Testnet"
    _IS_TEST_NET = True
    _BIP0044_COIN_TYPE = 1
    _BIP0032_VERSION_PUBLIC_KEY = 0x043587CF
    _BIP0032_VERSION_PRIVATE_KEY = 0x04358394
    _WIF_VERSION = 0xEF

    from .address import _TestAddress

    Address = _TestAddress
