from __future__ import annotations

from . import AbstractAmountModel, AbstractTransactionBroadcastStateModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..ui.gui import Application
    from ..wallet.mutable_tx import MutableTransaction


class TransactionBroadcastAvailableAmountModel(
        AbstractAmountModel,
        AbstractTransactionBroadcastStateModel):
    def __init__(self, application: Application, tx: MutableTransaction):
        super().__init__(application, tx)

    def _value(self) -> int:
        return self._tx.source_amount

    def _fiatValue(self) -> float:
        return self._coin.fiat_amount(self._tx.source_amount)
