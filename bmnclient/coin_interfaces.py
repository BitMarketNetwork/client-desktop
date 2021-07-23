from __future__ import annotations

from typing import TYPE_CHECKING

from .coins.abstract.coin import AbstractCoin
from .coins.utils import CoinUtils
from .database.tables import AddressListTable, CoinListTable, TxListTable
from .logger import Logger

if TYPE_CHECKING:
    from typing import Tuple
    from .database import Database
    from .network.query_scheduler import NetworkQueryScheduler
    from .utils.string import ClassStringKeyTuple


class _AbstractInterface:
    def __init__(
            self,
            *args,
            query_scheduler: NetworkQueryScheduler,
            database: Database,
            name_key_tuple: Tuple[ClassStringKeyTuple, ...],
            **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = Logger.classLogger(self.__class__, *name_key_tuple)
        self._query_scheduler = query_scheduler
        self._database = database


class CoinInterface(_AbstractInterface, AbstractCoin.Interface):
    def __init__(self, *args, coin: AbstractCoin, **kwargs) -> None:
        super().__init__(
            *args,
            coin=coin,
            name_key_tuple=CoinUtils.coinToNameKeyTuple(coin),
            **kwargs)

    def _save(self) -> None:
        try:
            with self._database.transaction() as cursor:
                self._database[CoinListTable].serialize(cursor, self._coin)
        except self._database.TransactionInEffectError:
            pass

    def afterSetEnabled(self) -> None:
        self._save()

    def afterSetHeight(self) -> None:
        pass

    def afterSetOffset(self) -> None:
        for address in self._coin.addressList:
            self._query_scheduler.updateCoinAddress(address)

    def afterSetStatus(self) -> None:
        pass

    def afterSetFiatRate(self) -> None:
        pass

    def afterUpdateAmount(self) -> None:
        pass

    def afterUpdateUtxoList(self) -> None:
        pass

    def beforeAppendAddress(self, address: AbstractCoin.Address) -> None:
        pass

    def afterAppendAddress(self, address: AbstractCoin.Address) -> None:
        if address.rowId <= 0:
            try:
                with self._database.transaction() as cursor:
                    self._database[AddressListTable].serialize(cursor, address)
            except self._database.TransactionInEffectError:
                pass
        self._query_scheduler.updateCoinAddress(address)

    def afterSetServerData(self) -> None:
        pass

    def afterStateChanged(self) -> None:
        self._save()


class AddressInterface(_AbstractInterface, AbstractCoin.Address.Interface):
    def __init__(self, *args, address: AbstractCoin.Address, **kwargs) -> None:
        super().__init__(
            *args,
            address=address,
            name_key_tuple=CoinUtils.addressToNameKeyTuple(address),
            **kwargs)

    def _save(self) -> None:
        try:
            with self._database.transaction() as cursor:
                self._database[AddressListTable].serialize(
                    cursor,
                    self._address)
        except self._database.TransactionInEffectError:
            pass

    def afterSetAmount(self) -> None:
        self._save()

    def afterSetLabel(self) -> None:
        self._save()

    def afterSetComment(self) -> None:
        self._save()

    def afterSetTxCount(self) -> None:
        self._save()

    def beforeAppendTx(self, tx: AbstractCoin.Tx) -> None:
        pass

    def afterAppendTx(self, tx: AbstractCoin.Tx) -> None:
        if tx.rowId <= 0:
            try:
                with self._database.transaction() as cursor:
                    self._database[TxListTable].serialize(
                        cursor,
                        self._address,
                        tx)
            except self._database.TransactionInEffectError:
                pass

    def afterSetUtxoList(self) -> None:
        pass

    def afterSetHistoryFirstOffset(self) -> None:
        self._save()

    def afterSetHistoryLastOffset(self) -> None:
        self._save()


class TxInterface(_AbstractInterface, AbstractCoin.Tx.Interface):
    def __init__(self, *args, tx: AbstractCoin.Tx, **kwargs) -> None:
        super().__init__(
            *args,
            tx=tx,
            name_key_tuple=CoinUtils.txToNameKeyTuple(tx),
            **kwargs)

    def _save(self) -> None:
        try:
            with self._database.transaction() as cursor:
                self._database[TxListTable].serialize(
                    cursor,
                    None,
                    self._tx)
        except self._database.TransactionInEffectError:
            pass

    def afterSetHeight(self) -> None:
        self._save()

    def afterSetTime(self) -> None:
        self._save()


class TxFactoryInterface(_AbstractInterface, AbstractCoin.TxFactory.Interface):
    def __init__(
            self,
            *args,
            factory: AbstractCoin.TxFactory,
            **kwargs) -> None:
        super().__init__(
            *args,
            factory=factory,
            name_key_tuple=CoinUtils.txFactoryToNameKeyTuple(factory),
            **kwargs)

    def afterUpdateState(self) -> None:
        pass

    def onBroadcast(self, mtx: AbstractCoin.TxFactory.MutableTx) -> None:
        self._query_scheduler.broadcastTx(mtx, self.onBroadcastFinished)

    def onBroadcastFinished(
            self,
            error_code: int,
            mtx: AbstractCoin.TxFactory.MutableTx) -> None:
        self._logger.debug("Result: error_code=%i, tx=%s", error_code, mtx.name)
