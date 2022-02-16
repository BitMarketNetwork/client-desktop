from __future__ import annotations

from .address import _Address, _TestAddress
from .script import _Script
from .tx_factory import _TxFactory
from ..abstract import Coin


class _Currency(Coin.Currency):
    _DECIMAL_SIZE = (0, 8)
    _FULL_NAME = "BTC"
    _UNIT = "BTC"


class Bitcoin(Coin):
    _SHORT_NAME = "btc"
    _FULL_NAME = "Bitcoin"
    _BIP0044_COIN_TYPE = 0
    # https://github.com/bitcoin/bitcoin/blob/master/src/chainparams.cpp
    _BIP0032_VERSION_PUBLIC_KEY = 0x0488b21e
    _BIP0032_VERSION_PRIVATE_KEY = 0x0488ade4
    _WIF_VERSION = 0x80

    Currency = _Currency
    Address = _Address
    TxFactory = _TxFactory
    Script = _Script


class BitcoinTest(Bitcoin):
    _SHORT_NAME = "btctest"
    _FULL_NAME = "Bitcoin Testnet"
    _IS_TEST_NET = True
    _BIP0044_COIN_TYPE = 1
    _BIP0032_VERSION_PUBLIC_KEY = 0x043587cf
    _BIP0032_VERSION_PRIVATE_KEY = 0x04358394
    _WIF_VERSION = 0xef

    Address = _TestAddress
