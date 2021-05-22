# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from .address import AddressModel
from .coin import CoinModel
from .tx import TxModel
from .tx_factory import TxFactoryModel
from ..coins.abstract.coin import AbstractCoin
from ..utils import NotImplementedInstance

if TYPE_CHECKING:
    from typing import Optional, TYPE_CHECKING
    from ..ui.gui import GuiApplication


class ModelsFactory(NotImplementedInstance):
    @staticmethod
    def create(
            application: GuiApplication,
            owner: object) -> Optional[object]:
        if isinstance(owner, AbstractCoin):
            return CoinModel(application, owner)

        if isinstance(owner, AbstractCoin.Address):
            return AddressModel(application, owner)

        if isinstance(owner, AbstractCoin.Tx):
            return TxModel(application, owner)

        if isinstance(owner, AbstractCoin.TxFactory):
            return TxFactoryModel(application, owner)

        return None
