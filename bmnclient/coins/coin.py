# JOK++
from __future__ import annotations

import math
from typing import Callable, List, Optional

from .address import AbstractAddress
from .currency import \
    AbstractCurrency, \
    FiatRate, \
    UsdFiatCurrency
from ..utils.meta import classproperty


class AbstractCoinModel:
    def beforeAppendAddress(self, address: AbstractAddress) -> None:
        raise NotImplementedError

    def afterAppendAddress(self, address: AbstractAddress) -> None:
        raise NotImplementedError

    def afterRefreshAmount(self) -> None:
        raise NotImplementedError

    def afterSetFiatRate(self) -> None:
        raise NotImplementedError


class AbstractCoin:
    _SHORT_NAME = ""
    _FULL_NAME = ""

    class Currency(AbstractCurrency):
        pass

    class Address(AbstractAddress):
        pass

    def __init__(
            self,
            *,
            model_factory: Optional[Callable[[object], object]] = None) -> None:
        self._fiat_rate = FiatRate(0, UsdFiatCurrency)
        self._amount = 0
        self._address_list = []

        self._model_factory = model_factory
        self._model: Optional[AbstractCoinModel] = self.model_factory(self)

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

    @property
    def addressList(self) -> List[Address]:
        return self._address_list

    def findAddressByName(self, name: str) -> Optional[Address]:
        name = name.strip().casefold()  # TODO tmp, old wrapper
        for address in self._address_list:
            if name == address.name.casefold():
                return address
        return None

    def putAddress(self, address: Address, *, check=True) -> bool:
        # TODO tmp, old wrapper
        if check and self.findAddressByName(address.name) is not None:  # noqa
            return False
        if self._model:
            self._model.beforeAppendAddress(address)
        self._address_list.append(address)
        if self._model:
            self._model.afterAppendAddress(address)
        self.refreshAmount()
        return True

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
        value //= self.Currency.decimalDivisor
        return value if self._fiat_rate.currency.isValidValue(value) else None

    def fromFiatAmount(self, value: int) -> Optional[int]:
        value *= self.Currency.decimalDivisor
        value = math.ceil(value / self._fiat_rate.value)
        return value if self.Currency.isValidValue(value) else None
