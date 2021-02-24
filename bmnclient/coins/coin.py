# JOK++
from __future__ import annotations

import math
from typing import Callable, List, Optional, Type

from .currency import \
    AbstractCurrency, \
    FiatCurrency, \
    FiatRate, \
    UsdFiatCurrency
from ..utils.meta import classproperty


class AbstractCoinModel:
    def beforeAppendAddress(self) -> None:
        raise NotImplementedError

    def afterAppendAddress(self) -> None:
        raise NotImplementedError

    def afterRefreshAmount(self) -> None:
        raise NotImplementedError

    def afterSetFiatRate(self) -> None:
        raise NotImplementedError


class AbstractCoin:
    _SHORT_NAME = ""
    _FULL_NAME = ""

    class _Currency(AbstractCurrency):
        pass

    from .address import AbstractAddress as _Address

    def __init__(
            self,
            *,
            model_factory: Optional[Callable[[object], object]] = None) -> None:
        self._model_factory = model_factory
        self._model: Optional[AbstractCoinModel] = self.model_factory(self)

        self._fiat_rate = FiatRate(0, UsdFiatCurrency)
        self._amount = 0
        self._address_list = []

    def model_factory(self, owner: object) -> Optional[object]:
        if self._model_factory:
            return self._model_factory(owner)
        return None

    @property
    def model(self) -> Optional[AbstractCoinModel]:
        return self._model

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

    @property
    def addressList(self) -> List[_Address]:
        return self._address_list

    def findAddressByName(self, name: str) -> Optional[_Address]:
        name = name.strip().casefold()  # TODO tmp, old wrapper
        for address in self._address_list:
            if name == address.name.casefold():
                return address
        return None

    def putAddress(self, address: _Address, *, check=True) -> bool:
        # TODO tmp, old wrapper
        if check and self.findAddressByName(address.name) is not None:  # noqa
            return False
        if self._model:
            self._model.beforeAppendAddress()
        self._address_list.append(address)
        if self._model:
            self._model.afterAppendAddress()
        return True

    @classproperty
    def currency(cls) -> Type[_Currency]: # noqa
        return cls._Currency

    @property
    def amount(self) -> int:
        return self._amount

    def refreshAmount(self) -> None:
        a = sum(a.balance for a in self._address_list if not a.readOnly)
        self._amount = a
        if self._model:
            self._model.afterRefreshAmount()

    @property
    def fiatRate(self) -> FiatRate:
        return self._fiat_rate

    @fiatRate.setter
    def fiatRate(self, fiat_rate: FiatRate) -> None:
        self._fiat_rate = fiat_rate
        if self._model:
            self._model.afterSetFiatRate()

    def toFiatAmount(self, value: Optional[int] = None) -> Optional[int]:
        if value is None:
            value = self._amount
        value *= self._fiat_rate.value
        value //= self._Currency.decimalDivisor
        return value if self._fiat_rate.currency.isValidValue(value) else None

    def fromFiatAmount(self, value: int) -> Optional[int]:
        value *= self._Currency.decimalDivisor
        value = math.ceil(value / self._fiat_rate.value)
        return value if self._Currency.isValidValue(value) else None


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
