# JOK++
from __future__ import annotations

from typing import Optional, Type

from .currency import \
    AbstractCurrency, \
    FiatRate, \
    FiatCurrency, \
    UsdFiatCurrency
from ..utils.meta import classproperty


class AbstractCoin:  # TODO ABCMeta
    _SHORT_NAME = ""
    _FULL_NAME = ""

    class _Currency(AbstractCurrency):
        pass

    from .address import AddressBase as _Address

    def __init__(self) -> None:
        self._fiat_rate = FiatRate(0, UsdFiatCurrency)
        self._amount = 0

    @classproperty
    def shortName(cls) -> str: # noqa
        return cls._SHORT_NAME

    @classproperty
    def fullName(cls) -> str: # noqa
        return cls._FULL_NAME

    @classproperty
    def iconPath(cls) -> str: # noqa
        # relative to "resources/images"
        return "coins/" + cls._SHORT_NAME + ".svg"

    @classproperty
    def address(cls) -> Type[_Address]: # noqa
        return cls._Address

    @classproperty
    def currency(cls) -> Type[_Currency]: # noqa
        return cls._Currency

    @property
    def amount(self) -> int:
        return self._amount

    @property
    def fiatRate(self) -> FiatRate:
        return self._fiat_rate

    @fiatRate.setter
    def fiatRate(self, fiat_rate: FiatRate) -> None:
        self._fiat_rate = fiat_rate

    def fiatAmount(self, value: Optional[int] = None) -> int:
        if value is None:
            value = self._amount
        value *= self._fiat_rate.value
        value //= self._Currency.decimalDivisor
        return value


class Bitcoin(AbstractCoin):
    _SHORT_NAME = "btc"
    _FULL_NAME = "Bitcoin"

    class _Currency(AbstractCoin._Currency):
        _DECIMAL_SIZE = (0, 8)
        _UNIT = "BTC"

    from .address import BitcoinAddress as _Address


class BitcoinTest(Bitcoin):
    _SHORT_NAME = "btctest"
    _FULL_NAME = "Bitcoin Testnet"

    class _Currency(Bitcoin._Currency):
        _UNIT = "BTC"

    from .address import BitcoinTestAddress as _Address


class Litecoin(Bitcoin):
    _SHORT_NAME = "ltc"
    _FULL_NAME = "Litecoin"

    class _Currency(Bitcoin._Currency):
        _UNIT = "LTC"

    from .address import LitecoinAddress as _Address
