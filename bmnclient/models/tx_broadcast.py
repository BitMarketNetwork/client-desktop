from __future__ import annotations

from typing import Final, TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    Signal as QSignal

from . import AbstractTransactionBroadcastStateModel
from .amount import AmountEditModel, AmountModel

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

    def _value(self) -> int:
        return self._tx.source_amount

    def _fiatValue(self) -> float:
        return self._coin.fiat_amount(self._tx.source_amount)


class TransactionBroadcastReceiverModel(AbstractTransactionBroadcastStateModel):
    _stateChanged: Final = QSignal()

    @QProperty(str, notify=_stateChanged)
    def addressName(self) -> str:
        return self._tx.receiver

    @addressName.setter
    def _setAddressName(self, name: str) -> None:
        self._tx.receiver = name
        self.refresh()

    @QProperty(bool, notify=_stateChanged)
    def isValidAddress(self) -> bool:
        return self._tx.receiver_valid
