# JOK+++
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide2.QtCore import \
    QBasicTimer, \
    QObject

from .api_v1.query import \
    CoinsInfoApiQuery, \
    ServerInfoApiQuery
from ..version import Timer

if TYPE_CHECKING:
    from PySide2.QtCore import QTimerEvent
    from .api_v1.query import AbstractServerApiQuery
    from .query_manager import NetworkQueryManager
    from ..application import CoreApplication


class NetworkQueryScheduler(QObject):
    _TIMER_INFO_LIST = (
        (
            "updateCurrentFiatCurrency",
            Timer.UPDATE_FIAT_CURRENCY_DELAY
        ), (
            "updateServerInfo",
            Timer.UPDATE_SERVER_INFO_DELAY
        ), (
            "updateCoinsInfo",
            Timer.UPDATE_COINS_INFO_DELAY
        ), (
            "getNextHdAddress",
            Timer.UPDATE_COINS_HD_DELAY
        )
    )

    def __init__(
            self,
            application: CoreApplication,
            manager: NetworkQueryManager) -> None:
        super().__init__()
        self._application = application
        self._manager = manager

        self._timer_list = {}
        for (callback, delay) in self._TIMER_INFO_LIST:
            self._timer_list[callback] = (
                QBasicTimer(),
                delay,
                getattr(self, callback)
            )

    def _putRepeatedApiQuery(
            self,
            query: AbstractServerApiQuery,
            timer_name: str,
            **kwargs) -> None:
        (timer, delay, callback) = self._timer_list[timer_name]
        timer.stop()
        query.putFinishedCallback(
            lambda _: timer.start(delay, self))
        self._manager.put(query, **kwargs)

    def timerEvent(self, event: QTimerEvent) -> None:
        for (timer, delay, callback) in self._timer_list.values():
            if event.timerId() == timer.timerId():
                callback()
                break

    def start(self) -> None:
        for (timer, delay, callback) in self._timer_list.values():
            callback()

    def updateCurrentFiatCurrency(self) -> None:
        service = self._application.fiatRateServiceList.current(
            self._application.coinList,
            self._application.fiatCurrencyList.current
        )
        self._putRepeatedApiQuery(
            service,
            "updateCurrentFiatCurrency",
            unique=True,
            high_priority=True)

    def updateServerInfo(self) -> None:
        self._putRepeatedApiQuery(
            ServerInfoApiQuery(),
            "updateServerInfo",
            unique=True)

    def updateCoinsInfo(self) -> None:
        self._putRepeatedApiQuery(
            CoinsInfoApiQuery(),
            "updateCoinsInfo",
            unique=True)

    def getNextHdAddress(self) -> None:
        for coin in self._application.coinList:
            pass

