from __future__ import annotations

from typing import TYPE_CHECKING

from .coins.abstract import Coin
from .database.tables import AddressListTable, TxListTable

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
    def afterSetOffset(self, value: str) -> None:
        for address in self._coin.addressList:
            self._query_scheduler.updateCoinAddress(address)
        super(_AbstractModel, self).afterSetOffset(value)

    def afterAppendAddress(self, address: Coin.Address) -> None:
        if address.rowId <= 0:
            try:
                with self._database.transaction() as cursor:
                    self._database[AddressListTable].serialize(cursor, address)
            except self._database.TransactionInEffectError:
                pass
        self._query_scheduler.updateCoinAddress(address)


class AddressModel(_AbstractModel, Coin.Address.Model):
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


class TxModel(_AbstractModel, Coin.Tx.Model):
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
    pass


class TxFactoryModel(_AbstractModel, Coin.TxFactory.Model):
    def onBroadcast(self, mtx: Coin.TxFactory.MutableTx) -> None:
        self._query_scheduler.broadcastTx(mtx, self.onBroadcastFinished)

    def onBroadcastFinished(
            self,
            error_code: int,
            mtx: Coin.TxFactory.MutableTx) -> None:
        self._logger.debug("Result: error_code=%i, tx=%s", error_code, mtx.name)
