from __future__ import annotations

from enum import auto
from typing import TYPE_CHECKING

from PySide6.QtCore import (
    Property as QProperty,
    QObject)

from . import AbstractModel
from .amount import AbstractAmountModel
from .list import (
    AbstractListModel,
    RoleEnum)
from ....coin_interfaces import TxIoInterface

if TYPE_CHECKING:
    from typing import Final, Optional
    from .. import QmlApplication
    from ....coins.abstract import Coin


class TxIoListModel(AbstractListModel):
    class Role(RoleEnum):
        ADDRESS: Final = auto()
        AMOUNT: Final = auto()

    ROLE_MAP: Final = {
        Role.ADDRESS: (
            b"address",
            lambda io: io.address.model),
        Role.AMOUNT: (
            b"amount",
            lambda io: io.model.amount)
    }
