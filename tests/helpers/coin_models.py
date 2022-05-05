from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

from bmnclient.coins.abstract import Coin
from bmnclient.database import Database

if TYPE_CHECKING:
    from bmnclient.coins.abstract import CoinObject, CoinObjectModel
    from .application import TestApplication


class CoinModel(Coin.Model):
    __DATABASE_NEXT_INDEX = itertools.count(start=1)

    def __init__(self, application: TestApplication, *, coin: Coin) -> None:
        # individual database for every coin instance
        db_file_path = application.tempPath
        db_file_path /= (
            "coin-{:s}-{:08d}.db"
            .format(coin.name, next(self.__class__.__DATABASE_NEXT_INDEX)))
        db_file_path.unlink(missing_ok=True)

        super().__init__(
            coin=coin,
            query_scheduler=application.networkQueryScheduler,
            database=Database(application, db_file_path))

    def __del__(self) -> None:
        self._database.close()

    @property
    def database(self) -> Database:
        if not self._database.isOpen and not self._database.open():
            raise RuntimeError("failed to open database")
        return self._database


class AddressModel(Coin.Address.Model):
    pass


class TxModel(Coin.Tx.Model):
    pass


class TxIoModel(Coin.Tx.Io.Model):
    pass


class UtxoModel(Coin.Tx.Utxo.Model):
    pass


class TxFactoryModel(Coin.TxFactory.Model):
    pass


class ModelsFactory:
    @staticmethod
    def create(
            application: TestApplication,
            owner: CoinObject) -> CoinObjectModel:
        if isinstance(owner, Coin):
            return CoinModel(application, coin=owner)

        if isinstance(owner, Coin.Address):
            return AddressModel(address=owner)

        if isinstance(owner, Coin.Tx):
            return TxModel(tx=owner)

        if isinstance(owner, Coin.Tx.Io):
            return TxIoModel(io=owner)

        if isinstance(owner, Coin.Tx.Utxo):
            return UtxoModel(utxo=owner)

        if isinstance(owner, Coin.TxFactory):
            return TxFactoryModel(factory=owner)

        raise TypeError
