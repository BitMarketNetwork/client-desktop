from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import (
    Property as QProperty,
    QObject)

from . import AbstractModel
from .abstract import AbstractTableModel
from .amount import AbstractAmountModel
from ....coins.abstract import Coin

if TYPE_CHECKING:
    from typing import Optional
    from .address import AddressModel
    from .. import QmlApplication


class TxIoAmountModel(AbstractAmountModel):
    def __init__(
            self,
            application: QmlApplication,
            io: Coin.Tx.Io) -> None:
        super().__init__(application, io.address.coin)
        self._io = io

    def _getValue(self) -> Optional[int]:
        return self._io.amount


class TxIoModel(Coin.Tx.Io.Model, AbstractModel):
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


class TxIoListModel(AbstractTableModel):
    pass
