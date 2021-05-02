from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Slot as QSlot

from ...models.tx_broadcast import TxBroadcastModel
from ...wallet import mutable_tx
from ...wallet.coins import CoinType

if TYPE_CHECKING:
    from . import Application

log = logging.getLogger(__name__)


class TxController(QObject):
    def __init__(self, application: Application, coin: CoinType) -> None:
        super().__init__()
        self._application = application
        self._coin = coin
        self._tx = mutable_tx.MutableTransaction(
            self._coin,
            self._application.feeManager)
        self._model = TxBroadcastModel(self._application, self._tx)

    @QProperty(QObject, constant=True)
    def model(self) -> TxBroadcastModel:
        return self._model

    @QSlot()
    def recalcSources(self):
        self._tx.recalc_sources()
        self._model.refresh()
