# JOK+++
from __future__ import annotations

import functools
from typing import TYPE_CHECKING

from PySide2.QtCore import \
    QBasicTimer, \
    QObject

from .api_v1.query import \
    CoinsInfoApiQuery, \
    HdAddressIteratorApiQuery, \
    SysinfoApiQuery
from ..version import Timer

if TYPE_CHECKING:
    from typing import Callable, Dict, Tuple
    from PySide2.QtCore import QTimerEvent
    from .api_v1.query import AbstractServerApiQuery
    from .query_manager import NetworkQueryManager
    from ..application import CoreApplication
    from ..coins.coin import AbstractCoin


class NetworkQueryTimer(QObject):
    def __init__(self, delay: int, callback: Callable[[], None]) -> None:
        super().__init__()
        self._timer = QBasicTimer()
        self._delay = delay
        self._callback = callback

    def start(self, *args, **kwargs) -> None:
        self._timer.start(self._delay, self)

    def stop(self) -> None:
        self._timer.stop()

    def timerEvent(self, event: QTimerEvent) -> None:
        assert event.timerId() == self._timer.timerId()
        self()

    def __call__(self, *args, **kwargs) -> None:
        self._callback()


class NetworkQueryScheduler:
    _TIMER_LIST = (
        (
            "updateCurrentFiatCurrency",
            Timer.UPDATE_FIAT_CURRENCY_DELAY
        ), (
            "updateSysinfo",
            Timer.UPDATE_SERVER_INFO_DELAY
        ), (
            "updateCoinsInfo",
            Timer.UPDATE_COINS_INFO_DELAY
        )
    )

    _COIN_TIMER_LIST = (
        (
            "updateHdAddressList",
            Timer.UPDATE_COINS_HD_ADDRESS_LIST_DELAY
        ),
    )

    def __init__(
            self,
            application: CoreApplication,
            manager: NetworkQueryManager) -> None:
        self._application = application
        self._manager = manager
        self._timer_list: Dict[str, NetworkQueryTimer] = {}

    def _createTimerList(self) -> None:
        assert len(self._timer_list) == 0

        for (callback, delay) in self._TIMER_LIST:
            name = callback + "/global"
            self._timer_list[name] = NetworkQueryTimer(
                delay,
                getattr(self, callback))

        for (callback, delay) in self._COIN_TIMER_LIST:
            for coin in self._application.coinList:
                name = callback + "/" + coin.shortName
                self._timer_list[name] = NetworkQueryTimer(
                    delay,
                    functools.partial(getattr(self, callback), coin))

    def _prepareTimer(self, name: Tuple[str, ...]) -> NetworkQueryTimer:
        timer = self._timer_list["/".join(name)]
        timer.stop()
        return timer

    def _putRepeatedApiQuery(
            self,
            query: AbstractServerApiQuery,
            timer_name: Tuple[str, ...],
            **kwargs) -> None:
        timer = self._prepareTimer(timer_name)
        query.putFinishedCallback(timer.start)
        self._manager.put(query, **kwargs)

    def start(self) -> None:
        self._createTimerList()
        for timer in self._timer_list.values():
            timer()

    def updateCurrentFiatCurrency(self) -> None:
        service = self._application.fiatRateServiceList.current(  # TODO self._application
            self._application.coinList,
            self._application.fiatCurrencyList.current
        )
        self._putRepeatedApiQuery(
            service,
            ("updateCurrentFiatCurrency", "global"),
            unique=True,
            high_priority=True)

    def updateSysinfo(self) -> None:
        self._putRepeatedApiQuery(
            SysinfoApiQuery(self._application),
            ("updateSysinfo", "global"),
            unique=True)

    def updateCoinsInfo(self) -> None:
        self._putRepeatedApiQuery(
            CoinsInfoApiQuery(self._application),
            ("updateCoinsInfo", "global"),
            unique=True)

    def updateHdAddressList(self, coin: AbstractCoin) -> None:
        timer = self._prepareTimer(("updateHdAddressList", coin.shortName))
        if coin.hdPath is None:
            timer.start()
        else:
            query = HdAddressIteratorApiQuery(
                self._application,
                coin,
                finished_callback=timer.start)
            self._manager.put(query)

