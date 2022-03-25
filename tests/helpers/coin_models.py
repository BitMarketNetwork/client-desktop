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

    def __init__(self, application: TestApplication, coin: Coin) -> None:
        # individual database for every coin instance
        db_file_path = application.tempPath
        db_file_path /= (
            "coin-{:s}-{:08d}.db"
            .format(coin.name, next(self.__class__.__DATABASE_NEXT_INDEX)))
        db_file_path.unlink(missing_ok=True)

        super().__init__(
            coin=coin,
            database=Database(application, db_file_path))

    def __del__(self) -> None:
        self._database.close()

    @property
    def database(self) -> Database:
        if not self._database.isOpen and not self._database.open():
            raise RuntimeError("failed to open database")
        return self._database


class AddressModel(Coin.Address.Model):
    def __init__(self, address: Coin.Address) -> None:
        super().__init__(address=address, database=address.coin.model.database)


class TxModel(Coin.Tx.Model):
    def __init__(self, tx: Coin.Tx) -> None:
        super().__init__(tx=tx, database=tx.coin.model.database)


class TxIoModel(Coin.Tx.Io.Model):
    def __init__(self, io: Coin.Tx.Io) -> None:
        super().__init__(io=io, database=io.coin.model.database)


class UtxoModel(Coin.Tx.Utxo.Model):
    def __init__(self, utxo: Coin.Tx.Utxo) -> None:
        super().__init__(utxo=utxo, database=utxo.coin.model.database)


class TxFactoryModel(Coin.TxFactory.Model):
    def __init__(self, factory: Coin.TxFactory) -> None:
        super().__init__(factory=factory, database=factory.coin.model.database)


class ModelsFactory:
    @staticmethod
    def create(
            application: TestApplication,
            owner: CoinObject) -> CoinObjectModel:
        if isinstance(owner, Coin):
            return CoinModel(application, owner)

        if isinstance(owner, Coin.Address):
            return AddressModel(owner)

        if isinstance(owner, Coin.Tx):
            return TxModel(owner)

        if isinstance(owner, Coin.Tx.Io):
            return TxIoModel(owner)

        if isinstance(owner, Coin.Tx.Utxo):
            return UtxoModel(owner)

        if isinstance(owner, Coin.TxFactory):
            return TxFactoryModel(owner)

        raise TypeError()
