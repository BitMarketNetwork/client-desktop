from __future__ import annotations

from .address import _BitcoinAddress, _BitcoinTestAddress
from .script import _BitcoinScript
from .tx_factory import _BitcoinTxFactory
from .. import abstract


class Bitcoin(abstract.Coin):
    _SHORT_NAME = "btc"
    _FULL_NAME = "Bitcoin"
    _BIP0044_COIN_TYPE = 0
    # https://github.com/bitcoin/bitcoin/blob/master/src/chainparams.cpp
    _BIP0032_VERSION_PUBLIC_KEY = 0x0488b21e
    _BIP0032_VERSION_PRIVATE_KEY = 0x0488ade4
    _WIF_VERSION = 0x80

    class Currency(abstract.Coin.Currency):
        _DECIMAL_SIZE = (0, 8)
        _FULL_NAME = "BTC"
        _UNIT = "BTC"

    Address = _BitcoinAddress
    TxFactory = _BitcoinTxFactory
    Script = _BitcoinScript


class BitcoinTest(Bitcoin):
    _SHORT_NAME = "btctest"
    _FULL_NAME = "Bitcoin Testnet"
    _IS_TEST_NET = True
    _BIP0044_COIN_TYPE = 1
    _BIP0032_VERSION_PUBLIC_KEY = 0x043587cf
    _BIP0032_VERSION_PRIVATE_KEY = 0x04358394
    _WIF_VERSION = 0xef

    Address = _BitcoinTestAddress
