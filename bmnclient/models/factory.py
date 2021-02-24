# JOK++
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .address import AddressModel
from .coin import CoinModel
from ..coins.address import AbstractAddress
from ..coins.coin import AbstractCoin

if TYPE_CHECKING:
    from ..ui.gui import Application


def modelFactory(application: Application, owner: object) -> Optional[object]:
    if isinstance(owner, AbstractCoin):
        return CoinModel(application, owner)

    if isinstance(owner, AbstractAddress):
        return AddressModel(application, owner)

    return None
