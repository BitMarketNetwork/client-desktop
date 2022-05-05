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
from ....coin_models import TxIoModel as _TxIoModel

if TYPE_CHECKING:
    from typing import Final, Optional
    from .address import AddressModel
    from .. import QmlApplication
    from ....coins.abstract import Coin


class TxIoAmountModel(AbstractAmountModel):
    def __init__(
            self,
            application: QmlApplication,
            io: Coin.Tx.Io) -> None:
        super().__init__(application, io.address.coin)
        self._io = io

    def _getValue(self) -> Optional[int]:
        return self._io.amount


class TxIoModel(_TxIoModel, AbstractModel):
    def __init__(self, application: QmlApplication, io: Coin.Tx.Io) -> None:
        super().__init__(application, io=io)

        self._amount_model = TxIoAmountModel(
            self._application,
            self._io)
        self.connectModelUpdate(self._amount_model)  # TODO

    @QProperty(QObject, constant=True)
    def address(self) -> AddressModel:
        return self._io.address.model

    @QProperty(QObject, constant=True)
    def amount(self) -> TxIoAmountModel:
        return self._amount_model


class TxIoListModel(AbstractListModel):
    class Role(RoleEnum):
        ADDRESS: Final = auto()
        AMOUNT: Final = auto()

    _ROLE_MAP: Final = {
        Role.ADDRESS: (
            b"address",
            lambda io: io.model.address),
        Role.AMOUNT: (
            b"amount",
            lambda io: io.model.amount)
    }
