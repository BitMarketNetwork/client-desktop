from __future__ import annotations

from .address import AddressBase
from .currency import AbstractCurrency


class CoinBase:
    _SHORT_NAME = ""
    _FULL_NAME = ""

    class Currency(AbstractCurrency):
        pass

    @property
    def shortName(self) -> str:
        return self._SHORT_NAME

    @property
    def fullName(self) -> str:
        return self._FULL_NAME

    @property
    def iconPath(self) -> str:
        # relative to "resources/images"
        return "coins/" + self._SHORT_NAME + ".svg"


class Bitcoin(CoinBase):
    _SHORT_NAME = "btc"
    _FULL_NAME = "Bitcoin"

    class Currency(CoinBase.Currency):
        _DECIMAL_SIZE = 8
        _UNIT = "BTC"

    from .address import BitcoinAddress as Address


class BitcoinTest(Bitcoin):
    _SHORT_NAME = "btctest"
    _FULL_NAME = "Bitcoin Testnet"

    class Currency(Bitcoin.Currency):
        _UNIT = "BTC"

    from .address import BitcoinTestAddress as Address


class Litecoin(Bitcoin):
    _SHORT_NAME = "ltc"
    _FULL_NAME = "Litecoin"

    class Currency(Bitcoin.Currency):
        _UNIT = "LTC"

    from .address import LitecoinAddress as Address
