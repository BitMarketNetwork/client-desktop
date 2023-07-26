from __future__ import annotations

from typing import TYPE_CHECKING

from ....coins.abstract import Coin
from ....utils import NotImplementedInstance
from .address import AddressModel
from .coin import CoinModel
from .tx import TxModel
from .tx_factory import TxFactoryModel
from .tx_io import TxIoModel
from .utxo import UtxoModel

if TYPE_CHECKING:
    from ....coins.abstract import CoinObject, CoinObjectModel
    from .. import QmlApplication


class ModelsFactory(NotImplementedInstance):
    @staticmethod
    def create(
        application: QmlApplication, owner: CoinObject
    ) -> CoinObjectModel:
        if isinstance(owner, Coin):
            return CoinModel(application, owner)

        if isinstance(owner, Coin.Address):
            return AddressModel(application, owner)

        if isinstance(owner, Coin.Tx):
            return TxModel(application, owner)

        if isinstance(owner, Coin.Tx.Io):
            return TxIoModel(application, owner)

        if isinstance(owner, Coin.Tx.Utxo):
            return UtxoModel(application, owner)

        if isinstance(owner, Coin.TxFactory):
            return TxFactoryModel(application, owner)

        raise TypeError(
            "model for class instance '{}' not found'".format(
                owner.__class__.__name__
            )
        )
