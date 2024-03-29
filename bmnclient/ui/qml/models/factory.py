from __future__ import annotations

from typing import TYPE_CHECKING

from .address import AddressModel
from .coin import CoinModel
from .tx import TxModel
from .tx_factory import TxFactoryModel
from .tx_io import TxIoModel
from ....coins.abstract import Coin
from ....utils import NotImplementedInstance

if TYPE_CHECKING:
    from typing import Optional, Union
    from .. import QmlApplication
    from ....coins.abstract import CoinObject, CoinObjectModel


class ModelsFactory(NotImplementedInstance):
    @staticmethod
    def create(
            application: QmlApplication,
            owner: CoinObject) -> Optional[CoinObjectModel]:
        if isinstance(owner, Coin):
            return CoinModel(application, owner)

        if isinstance(owner, Coin.Address):
            return AddressModel(application, owner)

        if isinstance(owner, Coin.Tx):
            return TxModel(application, owner)

        if isinstance(owner, Coin.Tx.Io):
            return TxIoModel(application, owner)

        if isinstance(owner, Coin.TxFactory):
            return TxFactoryModel(application, owner)

        return None
