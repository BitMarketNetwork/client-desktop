# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide2.QtCore import \
    QBasicTimer, \
    QObject

from .api_v1.query import \
    CoinMempoolIteratorApiQuery, \
    CoinsInfoApiQuery, \
    HdAddressIteratorApiQuery, \
    SysinfoApiQuery
from ..logger import Logger
from ..version import Timer

if TYPE_CHECKING:
    from typing import Callable, Dict, Final, Tuple
    from PySide2.QtCore import QTimerEvent
    from .query import AbstractQuery
    from .query_manager import NetworkQueryManager
    from ..application import CoreApplication
    from ..coins.abstract.coin import AbstractCoin


class NetworkQueryTimer(QObject):
    def __init__(
            self,
            delay: int,
            callback: Callable[[...], None],
            callback_args: tuple = ()) -> None:
        super().__init__()
        self._timer = QBasicTimer()
        self._delay = delay
        self._callback = callback
        self._callback_args = callback_args

    # noinspection PyUnusedLocal
    def start(self, *args, **kwargs) -> None:
        self._timer.start(self._delay, self)

    def stop(self) -> None:
        self._timer.stop()

    def timerEvent(self, event: QTimerEvent) -> None:
        assert event.timerId() == self._timer.timerId()
        self()

    def __call__(self) -> None:
        self._callback(*self._callback_args)


class NetworkQueryScheduler:
    GLOBAL_NAMESPACE: Final = "global"
    COINS_NAMESPACE: Final = "coins"
    NAMESPACE_SEPARATOR: Final = "/"

    _TIMER_LIST: Tuple[Tuple[str, int], ...] = (
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

    _COIN_TIMER_LIST: Tuple[Tuple[str, int], ...] = (
        (
            "updateCoinHdAddressList",
            Timer.UPDATE_COIN_HD_ADDRESS_LIST_DELAY
        ), (
            "updateCoinMempool",
            Timer.UPDATE_COIN_MEMPOOL_DELAY
        )
    )

    def __init__(
            self,
            application: CoreApplication,
            manager: NetworkQueryManager) -> None:
        self._application = application
        self._logger = Logger.getClassLogger(__name__, self.__class__)
        self._manager = manager
        self._timer_list: Dict[str, NetworkQueryTimer] = {}

    def _createTimerName(self, *name: str) -> str:
        return self.NAMESPACE_SEPARATOR.join(name)

    def _createTimerList(self) -> None:
        if len(self._timer_list) > 0:
            return

        for (callback_name, delay) in self._TIMER_LIST:
            name = self._createTimerName(self.GLOBAL_NAMESPACE, callback_name)
            self._timer_list[name] = NetworkQueryTimer(
                delay,
                getattr(self, callback_name))

        for (callback_name, delay) in self._COIN_TIMER_LIST:
            for coin in self._application.coinList:
                name = self._createTimerName(
                    self.COINS_NAMESPACE,
                    callback_name,
                    coin.name)
                self._timer_list[name] = NetworkQueryTimer(
                    delay,
                    getattr(self, callback_name),
                    (coin,))

    def _prepareTimer(self, *name: str) -> NetworkQueryTimer:
        timer = self._timer_list[self._createTimerName(*name)]
        timer.stop()
        return timer

    def _createRepeatingQuery(
            self,
            query: AbstractQuery,
            timer_name: Tuple[str, ...],
            **kwargs) -> None:
        timer = self._prepareTimer(*timer_name)
        query.putFinishedCallback(timer.start)
        self._manager.put(query, **kwargs)

    @property
    def manager(self) -> NetworkQueryManager:
        return self._manager

    def start(self, *namespace) -> None:
        self._createTimerList()
        if namespace:
            namespace = self._createTimerName(*namespace)
            namespace += self.NAMESPACE_SEPARATOR
        for (name, timer) in self._timer_list.items():
            if not namespace or name.startswith(namespace):
                self._logger.debug("Starting timer '%s'...", name)
                timer()

    def updateCurrentFiatCurrency(self) -> None:
        service = self._application.fiatRateServiceList.current(
            self._application.coinList,
            self._application.fiatCurrencyList.current
        )
        self._createRepeatingQuery(
            service,
            (self.GLOBAL_NAMESPACE, "updateCurrentFiatCurrency"),
            unique=True,
            high_priority=True)

    def updateSysinfo(self) -> None:
        self._createRepeatingQuery(
            SysinfoApiQuery(self._application.coinList),
            (self.GLOBAL_NAMESPACE, "updateSysinfo"),
            unique=True)

    def updateCoinsInfo(self) -> None:
        self._createRepeatingQuery(
            CoinsInfoApiQuery(self._application.coinList),
            (self.GLOBAL_NAMESPACE, "updateCoinsInfo"),
            unique=True)

    def updateCoinHdAddressList(self, coin: AbstractCoin) -> None:
        timer = self._prepareTimer(
            self.COINS_NAMESPACE,
            "updateCoinHdAddressList",
            coin.name)
        if coin.hdPath is None:
            timer.start()
            return

        query = HdAddressIteratorApiQuery(
            coin,
            query_manager=self._manager,
            finished_callback=timer.start)
        self._manager.put(query)

    def updateCoinMempool(self, coin: AbstractCoin) -> None:
        timer = self._prepareTimer(
            self.COINS_NAMESPACE,
            "updateCoinMempool",
            coin.name)
        if len(coin.addressList) <= 0:
            timer.start()
            return

        query = CoinMempoolIteratorApiQuery(
            coin,
            query_manager=self._manager,
            finished_callback=timer.start)
        self._manager.put(query)
