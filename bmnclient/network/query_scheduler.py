from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import \
    QBasicTimer, \
    QObject

from .api_v1.query import \
    AbstractApiQuery, \
    AddressInfoApiQuery, \
    AddressTxIteratorApiQuery, \
    AddressUtxoIteratorApiQuery, \
    CoinMempoolIteratorApiQuery, \
    CoinsInfoApiQuery, \
    HdAddressIteratorApiQuery, \
    SysinfoApiQuery, \
    TxBroadcastApiQuery
from .services.github import GithubNewReleasesApiQuery
from .query_manager import NetworkQueryManager
from ..logger import Logger
from ..version import Timer

if TYPE_CHECKING:
    from typing import Callable, Dict, Final, List, Tuple
    from PySide6.QtCore import QTimerEvent
    from .query import AbstractQuery
    from ..application import CoreApplication
    from ..coins.abstract import Coin


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

    @property
    def delay(self) -> int:
        return self._delay

    def start(self) -> None:
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
            "updateNewReleasesInfo",
            Timer.UPDATE_NEW_RELEASES_DELAY
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
        self._logger = Logger.classLogger(self.__class__, (None, manager.name))
        self._manager = manager
        self._timer_list: Dict[str, NetworkQueryTimer] = {}

        self._pending_queue: Dict[str, List] = {
            "coin_address": []
        }

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

    def __queryFinishedCallback(
            self,
            timer: NetworkQueryTimer,
            query: AbstractQuery) -> None:
        if query.nextQuery is None:
            timer.start()
            self._logger.debug(
                "Restarting timer after last query '%s', delay %ims.",
                str(query),
                timer.delay)

    def _putQuery(
            self,
            query: AbstractQuery, **kwargs) -> NetworkQueryManager.PutStatus:
        if isinstance(query, AbstractApiQuery):
            query.setServer(
                self._application.serverList.currentServerUrl,
                self._application.serverList.allowInsecure)
        return self._manager.put(query, **kwargs)

    def _createRepeatingQuery(
            self,
            query: AbstractQuery,
            timer_name: Tuple[str, ...],
            high_priority: bool) -> None:
        timer = self._prepareTimer(*timer_name)
        query.appendFinishedCallback(
            lambda q: self.__queryFinishedCallback(timer, q))
        status = self._putQuery(
            query,
            unique=True,
            high_priority=high_priority)
        if status == NetworkQueryManager.PutStatus.ERROR_NOT_UNIQUE:
            timer.start()

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
            True)

    def updateSysinfo(self) -> None:
        self._createRepeatingQuery(
            SysinfoApiQuery(self._application.coinList),
            (self.GLOBAL_NAMESPACE, "updateSysinfo"),
            False)

    def updateNewReleasesInfo(self) -> None:
        self._createRepeatingQuery(
            GithubNewReleasesApiQuery(),
            (self.GLOBAL_NAMESPACE, "updateNewReleasesInfo"),
            False)

    def updateCoinsInfo(self) -> None:
        self._createRepeatingQuery(
            CoinsInfoApiQuery(self._application.coinList),
            (self.GLOBAL_NAMESPACE, "updateCoinsInfo"),
            False)

    def updateCoinHdAddressList(self, coin: Coin) -> None:
        self._createRepeatingQuery(
            HdAddressIteratorApiQuery(coin),
            (self.COINS_NAMESPACE, "updateCoinHdAddressList", coin.name),
            False)

    def updateCoinMempool(self, coin: Coin) -> None:
        self._createRepeatingQuery(
            CoinMempoolIteratorApiQuery(coin),
            (self.COINS_NAMESPACE, "updateCoinMempool", coin.name),
            False)

    def updateCoinAddress(self, address: Coin.Address) -> None:
        query = AddressTxIteratorApiQuery(
            address,
            mode=AddressTxIteratorApiQuery.Mode.FULL,
            first_offset=address.coin.offset,
            last_offset=address.historyFirstOffset)
        query.appendFinishedCallback(
            lambda q: self.__pendingUpdateCoinAddress(q, address))

        status = self._putQuery(query, unique=True)

        # this AddressTxIteratorApiQuery already in queue, wait...
        # will be process by
        if status == NetworkQueryManager.PutStatus.ERROR_NOT_UNIQUE:
            queue = self._pending_queue["coin_address"]
            if address not in queue:
                queue.append(address)
        else:
            self._putQuery(AddressInfoApiQuery(address))
            # TODO run if balance
            self._putQuery(AddressUtxoIteratorApiQuery(address))

    def __pendingUpdateCoinAddress(
            self,
            query: AddressTxIteratorApiQuery,
            address: Coin.Address) -> None:
        if query.nextQuery is not None:
            return
        queue = self._pending_queue["coin_address"]
        if address in queue:
            queue.remove(address)
            self.updateCoinAddress(address)

    def broadcastTx(
            self,
            mtx: Coin.TxFactory.MutableTx,
            finished_callback: Callable[
                [int, Coin.TxFactory.MutableTx],
                None]) -> bool:
        query = TxBroadcastApiQuery(mtx)
        query.appendFinishedCallback(
            lambda q: self.__onBroadcastTxFinished(q, mtx, finished_callback))
        status = self._putQuery(query, high_priority=True, unique=True)
        if status == NetworkQueryManager.PutStatus.SUCCESS:
            return True
        finished_callback(-1, mtx)  # TODO correct error code
        return False

    def __onBroadcastTxFinished(
            self,
            query: TxBroadcastApiQuery,
            mtx: Coin.TxFactory.MutableTx,
            finished_callback: Callable[
                [int, Coin.TxFactory.MutableTx],
                None]) -> None:
        if query.isSuccess and query.result is not None:
            if query.result.txName != mtx.name:
                self._logger.warning(
                    "Server gives transaction: '%s', but was sent '%s'.",
                    query.result.txName,
                    mtx.name)
            self.updateCoinMempool(mtx.coin)
            finished_callback(0, mtx)
        else:
            # TODO convert error code from response
            finished_callback(2005, mtx)
