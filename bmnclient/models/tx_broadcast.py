from __future__ import annotations

from typing import Final, TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    Signal as QSignal, \
    Slot as QSlot

from . import AbstractTransactionBroadcastStateModel
from .amount import AmountInputModel, AmountModel

if TYPE_CHECKING:
    from ..ui.gui import Application
    from ..wallet.mutable_tx import MutableTransaction


class TransactionBroadcastAvailableAmountModel(AmountModel):
    def __init__(
            self,
            application: Application,
            tx: MutableTransaction) -> None:
        super().__init__(application, tx.coin)
        self._tx = tx

    def _getValue(self) -> int:
        return self._tx.source_amount


class TransactionBroadcastAmountModel(AmountInputModel):
    def __init__(
            self,
            application: Application,
            tx: MutableTransaction) -> None:
        super().__init__(application, tx.coin)
        self._tx = tx

    def _getValue(self) -> int:
        return self._tx.amount

    def _setValue(self, value: int) -> bool:
        if value >= 0:
            self._tx.amount = value
            return True
        return False

    def _setDefaultValue(self) -> bool:
        self._tx.set_max()


class TransactionBroadcastReceiverModel(AbstractTransactionBroadcastStateModel):
    stateChanged: Final = QSignal()

    @QProperty(str, notify=stateChanged)
    def addressName(self) -> str:
        return self._tx.receiver

    @addressName.setter
    def _setAddressName(self, name: str) -> None:
        self._tx.receiver = name
        self.refresh()

    @QProperty(bool, notify=stateChanged)
    def isValidAddress(self) -> bool:
        return self._tx.receiver_valid
