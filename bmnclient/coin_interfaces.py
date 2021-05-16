# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from .coins.abstract.coin import AbstractCoin
from .coins.utils import CoinLoggerUtils
from .logger import Logger

if TYPE_CHECKING:
    from typing import Optional
    from .wallet.mtx_impl import Mtx
    from .network.query_scheduler import NetworkQueryScheduler
    from .database.db_wrapper import Database


class _AbstractInterface:
    def __init__(
            self,
            *args,
            query_scheduler: NetworkQueryScheduler,
            database: Database,
            name_suffix: Optional[str] = None,
            **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = Logger.getClassLogger(
            __name__,
            self.__class__,
            name_suffix)
        self._query_scheduler = query_scheduler
        self._database = database


class CoinInterface(_AbstractInterface, AbstractCoin.Interface):
    def __init__(self, *args, coin: AbstractCoin, **kwargs) -> None:
        super().__init__(
            *args,
            coin=coin,
            name_suffix=CoinLoggerUtils.coinToNameSuffix(coin),
            **kwargs)

    def afterSetEnabled(self) -> None:
        if self._database.isLoaded:
            self._database.updateCoin(self._coin)

    def afterSetHeight(self) -> None:
        pass

    def afterSetOffset(self) -> None:
        for address in self._coin.addressList:
            self._query_scheduler.updateCoinAddress(address)

    def afterSetStatus(self) -> None:
        pass

    def afterSetFiatRate(self) -> None:
        pass

    def afterRefreshAmount(self) -> None:
        pass

    def afterRefreshUtxoList(self) -> None:
        pass

    def beforeAppendAddress(self, address: AbstractCoin.Address) -> None:
        pass

    def afterAppendAddress(self, address: AbstractCoin.Address) -> None:
        if self._database.isLoaded and address.rowId is None:
            self._database.updateCoinAddress(address)
        self._query_scheduler.updateCoinAddress(address)

    def afterSetServerData(self) -> None:
        pass

    def afterStateChanged(self) -> None:
        if self._database.isLoaded:
            self._database.updateCoin(self._coin)


class AddressInterface(_AbstractInterface, AbstractCoin.Address.Interface):
    def __init__(self, *args, address: AbstractCoin.Address, **kwargs) -> None:
        super().__init__(
            *args,
            address=address,
            name_suffix=CoinLoggerUtils.addressToNameSuffix(address),
            **kwargs)

    def afterSetAmount(self) -> None:
        if self._database.isLoaded:
            self._database.updateCoinAddress(self._address)

    def afterSetLabel(self) -> None:
        if self._database.isLoaded:
            self._database.updateCoinAddress(self._address)

    def afterSetComment(self) -> None:
        if self._database.isLoaded:
            self._database.updateCoinAddress(self._address)

    def afterSetTxCount(self) -> None:
        if self._database.isLoaded:
            self._database.updateCoinAddress(self._address)

    def beforeAppendTx(self, tx: AbstractCoin.Tx) -> None:
        pass

    def afterAppendTx(self, tx: AbstractCoin.Tx) -> None:
        if self._database.isLoaded and tx.height >= 0:
            self._database.updateCoinAddressTx(self._address, tx)

    def afterSetUtxoList(self) -> None:
        pass

    def afterSetHistoryFirstOffset(self) -> None:
        if self._database.isLoaded:
            self._database.updateCoinAddress(self._address)

    def afterSetHistoryLastOffset(self) -> None:
        if self._database.isLoaded:
            self._database.updateCoinAddress(self._address)


class TxInterface(_AbstractInterface, AbstractCoin.Tx.Interface):
    def __init__(self, *args, tx: AbstractCoin.Tx, **kwargs) -> None:
        super().__init__(
            *args,
            tx=tx,
            name_suffix=CoinLoggerUtils.txToNameSuffix(tx),
            **kwargs)

    def afterSetHeight(self) -> None:
        # TODO slow, bad
        for address in self._tx.coin.addressList:
            if self._tx in address.txList:
                self._database.updateCoinAddressTx(address, self._tx)

    def afterSetTime(self) -> None:
        # TODO slow, bad
        for address in self._tx.coin.addressList:
            if self._tx in address.txList:
                self._database.updateCoinAddressTx(address, self._tx)


class MutableTxInterface(_AbstractInterface, AbstractCoin.MutableTx.Interface):
    def __init__(self, *args, tx: AbstractCoin.MutableTx, **kwargs) -> None:
        super().__init__(
            *args,
            tx=tx,
            name_suffix=CoinLoggerUtils.coinToNameSuffix(tx.coin),
            **kwargs)

    def onBroadcast(self, tx: Mtx) -> None:
        self._query_scheduler.broadcastTx(tx, self.onBroadcastFinished)

    def onBroadcastFinished(self, error_code: int, tx: Mtx) -> None:
        self._logger.debug("Result: error_code=%i, tx=%s", error_code, tx.id)
