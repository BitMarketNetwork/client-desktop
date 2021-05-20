# JOK4
from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

from PySide2.QtCore import QObject

from ..query import AbstractJsonQuery
from ...coins.currency import \
    EuroFiatCurrency, \
    FiatCurrency, \
    FiatRate, \
    UsdFiatCurrency
from ...config import UserConfig, UserConfigStaticList
from ...utils.class_property import classproperty

if TYPE_CHECKING:
    from typing import Dict, Final, Iterator, List, Optional, Type, Union
    from ...application import CoreApplication
    from ...coins.list import CoinList


class AbstractFiatRateService(AbstractJsonQuery):
    _SHORT_NAME = ""
    _FULL_NAME = ""
    _COIN_MAP: Final = {  # local: service
        "btc": "bitcoin",
        "btctest": "bitcoin",
        "ltc": "litecoin"
    }
    _CURRENCY_MAP = {  # local: service
        UsdFiatCurrency: "usd",
        EuroFiatCurrency: "eur"
    }

    def __init__(
            self,
            coin_list: CoinList,
            currency_type: Type[FiatCurrency] = UsdFiatCurrency) -> None:
        super().__init__(name_key_tuple=((None, currency_type.unit), ))
        self._buffer = BytesIO()

        self._coin_list = coin_list
        self._coin_name_list = self._createCoinNameList()

        self._currency_type = currency_type
        self._currency_name = self._createFiatCurrencyName()

    def isEqualQuery(self, other: AbstractFiatRateService) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.name == other.name
            and self._currency_type is other._currency_type
        )

    @classproperty
    def name(cls) -> str:  # noqa
        return cls._SHORT_NAME

    @classproperty
    def fullName(cls) -> str:  # noqa
        return cls._FULL_NAME

    def _processResponse(self, response: Optional[dict]) -> None:
        if (
                not self.isSuccess
                or response is None
                or self.statusCode != 200
                or self.isDummyRequest
        ):
            if not self.isDummyRequest:
                self._logger.warning(
                    "Invalid response from '{}' Service."
                    .format(self._FULL_NAME))
            response = {}

        for coin in self._coin_list:
            name = self._COIN_MAP.get(coin.name)
            if name:
                fiat_rate = self._getFiatRate(name, response)
                if fiat_rate is None:
                    fiat_rate = 0
                    if self.url is not None:
                        self._logger.warning(
                            "Failed to parse fiat rate for '{}'."
                            .format(coin.fullName))
                coin.fiatRate = FiatRate(fiat_rate, self._currency_type)

    def _createCoinNameList(self) -> List[str]:
        result = []
        for coin in self._coin_list:
            name = self._COIN_MAP.get(coin.name)
            if name:
                if name not in result:
                    result.append(name)
            else:
                self._logger.warning(
                    "Fiat rate for '{}' not supported by '{}' Service."
                    .format(coin.fullName, self._FULL_NAME))

        if not result:
            self._logger.warning(
                "Required fiat rates not supported by '{}' Service."
                .format(self._FULL_NAME))

        return result

    def _createFiatCurrencyName(self) -> Optional[str]:
        result = None
        for (currency_type, name) in self._CURRENCY_MAP.items():
            if currency_type is self._currency_type and name:
                result = name
                break

        if not result:
            self._logger.warning(
                "Required fiat currency '{}' not supported by '{}' Service."
                .format(self._currency_type.name, self._FULL_NAME))

        return result

    def _getFiatRate(self, coin_name: str, data: dict) -> Optional[int]:
        raise NotImplementedError


class NoneFiatRateService(AbstractFiatRateService):
    _SHORT_NAME: Final = "none"
    _FULL_NAME: Final = QObject().tr("-- None --")
    _DEFAULT_BASE_URL: Final = None

    def _getFiatRate(self, coin_name: str, data: dict) -> Optional[int]:
        return 0


class RandomFiatRateService(AbstractFiatRateService):
    _SHORT_NAME: Final = "random"
    _FULL_NAME: Final = "-- random value --"
    _DEFAULT_BASE_URL: Final = None

    def _getFiatRate(self, coin_name: str, data: dict) -> Optional[int]:
        from random import randrange
        return randrange(0, 1000000) * 10


class CoinGeckoFiatRateService(AbstractFiatRateService):
    _SHORT_NAME: Final = "coingecko"
    _FULL_NAME: Final = "CoinGecko"
    _DEFAULT_BASE_URL: Final = "https://api.coingecko.com/api/v3/simple/price"

    @property
    def arguments(self) -> Dict[str, Union[int, str]]:
        return {
            "ids": ",".join(self._coin_name_list),
            "vs_currencies": self._currency_name
        }

    def _getFiatRate(self, coin_name: str, data: dict) -> Optional[int]:
        try:
            value = data[coin_name][self._currency_name]
            return int(value * self._currency_type.decimalDivisor)
        except (KeyError, TypeError):
            return None


class FiatRateServiceList(UserConfigStaticList):
    def __init__(self, application: CoreApplication) -> None:
        service_list = (
            NoneFiatRateService,
            CoinGeckoFiatRateService,
        )

        if application.isDebugMode:
            service_list = (RandomFiatRateService, ) + service_list

        super().__init__(
            application.userConfig,
            UserConfig.KEY_SERVICES_FIAT_RATE,
            service_list,
            default_index=1,
            item_property="name")
        self._logger.debug(
            "Current fiat rate service is '%s'.",
            self.current.fullName)

    def __iter__(self) -> Iterator[Type[AbstractFiatRateService]]:
        return super().__iter__()

    def __getitem__(
            self,
            value: Union[str, int]) -> Optional[Type[AbstractFiatRateService]]:
        return super().__getitem__(value)

    @property
    def current(self) -> Type[AbstractFiatRateService]:
        return super().current
