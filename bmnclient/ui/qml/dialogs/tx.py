from __future__ import annotations

from typing import TYPE_CHECKING

from . import AbstractDialog
from ....coins.abstract import Coin

if TYPE_CHECKING:
    from . import DialogManager


class TxBroadcastPendingDialog(AbstractDialog):
    _QML_NAME = "BTxBroadcastPendingDialog"

    def __init__(
            self,
            manager: DialogManager,
            mtx: Coin.TxFactory.MutableTx) -> None:
        super().__init__(manager, mtx)
        self._mtx = mtx
        self._qml_properties["tx"] = self._mtx.model
        self._qml_properties["coin"] = self._mtx.coin.model

    def onRejected(self) -> None:
        self._manager.context.emit()
