from __future__ import annotations

from typing import TYPE_CHECKING

from .coins.abstract import Coin
from .coins.utils import CoinUtils
from .database.tables import AddressListTable, CoinListTable, TxListTable

if TYPE_CHECKING:
    from .network.query_scheduler import NetworkQueryScheduler


class _AbstractModel:
    def __init__(
            self,
            *args,
            query_scheduler: NetworkQueryScheduler,
            **kwargs):
        super().__init__(*args, **kwargs)
        self._query_scheduler = query_scheduler


class CoinModel(_AbstractModel, Coin.Model):
    def __init__(self, *args, coin: Coin, **kwargs) -> None:
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

    def afterSetOffset(self) -> None:
        for address in self._coin.addressList:
            self._query_scheduler.updateCoinAddress(address)

    def afterAppendAddress(self, address: Coin.Address) -> None:
        if address.rowId <= 0:
            try:
                with self._database.transaction() as cursor:
                    self._database[AddressListTable].serialize(cursor, address)
            except self._database.TransactionInEffectError:
                pass
        self._query_scheduler.updateCoinAddress(address)

    def afterStateChanged(self) -> None:
        self._save()


class AddressModel(_AbstractModel, Coin.Address.Model):
    def __init__(self, *args, address: Coin.Address, **kwargs) -> None:
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

    def afterSetLabel(self) -> None:
        self._save()

    def afterSetComment(self) -> None:
        self._save()

    def afterSetTxCount(self) -> None:
        self._save()

    def afterAppendTx(self, tx: Coin.Tx) -> None:
        if tx.rowId <= 0:
            try:
                with self._database.transaction() as cursor:
                    self._database[TxListTable].serialize(
                        cursor,
                        self._address,
                        tx)
            except self._database.TransactionInEffectError:
                pass

    def afterSetHistoryFirstOffset(self) -> None:
        self._save()

    def afterSetHistoryLastOffset(self) -> None:
        self._save()


class TxModel(_AbstractModel, Coin.Tx.Model):
    def __init__(self, *args, tx: Coin.Tx, **kwargs) -> None:
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


class TxIoModel(_AbstractModel, Coin.Tx.Io.Model):
    def __init__(self, *args, io: Coin.Tx.Io, **kwargs) -> None:
        super().__init__(
            *args,
            io=io,
            name_key_tuple=CoinUtils.txIoToNameKeyTuple(io),
            **kwargs)


class TxFactoryModel(_AbstractModel, Coin.TxFactory.Model):
    def __init__(self, *args, factory: Coin.TxFactory, **kwargs) -> None:
        super().__init__(
            *args,
            factory=factory,
            name_key_tuple=CoinUtils.txFactoryToNameKeyTuple(factory),
            **kwargs)

    def afterUpdateState(self) -> None:
        pass

    def afterSetInputAddress(self) -> None:
        pass

    def afterSetReceiverAddress(self) -> None:
        pass

    def onBroadcast(self, mtx: Coin.TxFactory.MutableTx) -> None:
        self._query_scheduler.broadcastTx(mtx, self.onBroadcastFinished)

    def onBroadcastFinished(
            self,
            error_code: int,
            mtx: Coin.TxFactory.MutableTx) -> None:
        self._logger.debug("Result: error_code=%i, tx=%s", error_code, mtx.name)
