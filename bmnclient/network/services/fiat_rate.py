# JOK++
from __future__ import annotations

import json
from io import BytesIO
from json import JSONDecodeError
from typing import Final, List, Optional, TYPE_CHECKING, Type

from PySide2.QtCore import QObject

from ...coins.currency import FiatCurrency, FiatRate, UsdFiatCurrency
from ...config import UserConfig
from ...logger import Logger
from ...server.net_cmd import BaseNetworkCommand
from ...utils.meta import classproperty
from ...utils.static_list import UserStaticList

if TYPE_CHECKING:
    from ...application import CoreApplication
    from ...coins.list import CoinList


class FiatRateService(BaseNetworkCommand):
    _SHORT_NAME = ""
    _FULL_NAME = ""
    _COIN_MAP: Final = {  # local: service
        "btc": "bitcoin",
        "btctest": "bitcoin",
        "ltc": "litecoin"
    }
    _CURRENCY_MAP = {  # local: service
        UsdFiatCurrency: "usd"
    }

    def __init__(
            self,
            coin_list: CoinList,
            currency: Type[FiatCurrency] = UsdFiatCurrency) -> None:
        super().__init__(None)
        self._buffer = BytesIO()

        self._coin_list = coin_list
        self._coin_name_list = self._createCoinNameList()

        self._currency = currency
        self._currency_name = self._createFiatCurrencyName()

    @classproperty
    def shortName(cls) -> str:  # noqa
        return cls._SHORT_NAME

    @classproperty
    def fullName(cls) -> str:  # noqa
        return cls._FULL_NAME

    def createRequestData(self) -> Optional[dict]:
        if not self._coin_name_list or not self._currency_name:
            return None
        return self._createRequestData()

    def onResponseData(self, data: bytes) -> bool:
        # TODO download limit
        self._buffer.write(data)
        return True

    def onResponseFinished(self) -> None:
        result = self._buffer.getvalue()
        self._buffer.close()
        self._logger.debug(result.decode(encoding="utf-8"))

        if self.url is None:
            result = {}
        else:
            try:
                result = json.loads(result)
            except JSONDecodeError as e:
                self._logger.warning(
                    "Failed to read response. "
                    + Logger.jsonDecodeErrorToString(e))
                return

        for coin in self._coin_list:
            name = self._COIN_MAP.get(coin.shortName)
            if name:
                fiat_rate = self._getFiatRate(name, result)
                if fiat_rate is None:
                    fiat_rate = 0
                    self._logger.warning(
                        "Failed to parse fiat rate for \"{}\"."
                        .format(coin.fullName))
                coin.fiatRate = FiatRate(fiat_rate, self._currency)

    def _createCoinNameList(self) -> List[str]:
        result = []
        for coin in self._coin_list:
            name = self._COIN_MAP.get(coin.shortName)
            if name:
                if name not in result:
                    result.append(name)
            else:
                self._logger.warning(
                    "Fiat rate for \"{}\" not supported by \"{}\" Service."
                    .format(coin.fullName, self._FULL_NAME))

        if not result:
            self._logger.warning(
                "Required fiat rates not supported by \"{}\" Service."
                .format(self._FULL_NAME))

        return result

    def _createFiatCurrencyName(self) -> Optional[str]:
        result = None
        for (currency, name) in self._CURRENCY_MAP.items():
            if currency is self._currency and name:
                result = name
                break

        if not result:
            self._logger.warning(
                "Required fiat currency \"{}\" not supported by \"{}\" Service."
                .format(self._currency.name, self._FULL_NAME))

        return result

    def _createRequestData(self) -> Optional[dict]:
        raise NotImplementedError

    def _getFiatRate(self, coin_name: str, data: dict) -> Optional[int]:
        raise NotImplementedError


class NoneFiatRateService(FiatRateService):
    _SHORT_NAME: Final = "none"
    _FULL_NAME: Final = QObject().tr("-- None --")
    _BASE_URL: Final = None

    def _createRequestData(self) -> Optional[dict]:
        return {}

    def _getFiatRate(self, coin_name: str, data: dict) -> Optional[int]:
        return 0


class CoinGeckoFiatRateService(FiatRateService):
    _SHORT_NAME: Final = "coingecko"
    _FULL_NAME: Final = "CoinGecko"
    _BASE_URL: Final = "https://api.coingecko.com/api/v3/simple/price"

    def _createRequestData(self) -> Optional[dict]:
        return {
            "ids": ",".join(self._coin_name_list),
            "vs_currencies": self._currency_name,
        }

    def _getFiatRate(self, coin_name: str, data: dict) -> Optional[int]:
        try:
            value = data[coin_name][self._currency_name]
            return int(value * self._currency.decimalDivisor)
        except (KeyError, TypeError):
            return None


class FiatRateServiceList(UserStaticList):
    ItemType = Type[FiatRateService]

    def __init__(self, application: CoreApplication) -> None:
        super().__init__(
            application.userConfig,
            UserConfig.KEY_SERVICES_FIAT_RATE,
            [
                NoneFiatRateService,
                CoinGeckoFiatRateService,
            ],
            default_index=1,
            item_property="shortName")
        self._logger.debug(
            "Current fiat rate service is \"%s\".",
            self._list[self._current_index].fullName)
