# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from .address import AddressModel
from .coin import CoinModel
from .mutable_tx import MutableTxModel
from .tx import TxModel
from ..coins.abstract.coin import AbstractCoin

if TYPE_CHECKING:
    from typing import Optional, TYPE_CHECKING
    from ..ui.gui import Application


def modelFactory(application: Application, owner: object) -> Optional[object]:
    if isinstance(owner, AbstractCoin):
        return CoinModel(application, owner)

    if isinstance(owner, AbstractCoin.Address):
        return AddressModel(application, owner)

    if isinstance(owner, AbstractCoin.Tx):
        return TxModel(application, owner)

    if isinstance(owner, AbstractCoin.MutableTx):
        return MutableTxModel(application, owner)

    return None
