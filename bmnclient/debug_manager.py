from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PySide2.QtCore import \
    QObject, \
    Slot as QSlot

if TYPE_CHECKING:
    from . import Application


class DebugManager(QObject):
    def __init__(self, application: Application):
        super().__init__()
        self._application = application

    @QSlot()
    def poll(self) -> None:
        self._application.networkThread.poll_coins()

    @QSlot()
    def stopPolling(self) -> None:
        self._application.networkThread.stop_poll()

    @QSlot()
    def retrieveFee(self) -> None:
        self._application.networkThread.retrieve_fee()

    @QSlot(int)
    def kill(self, sig: int):
        os.kill(os.getpid(), sig)

    @QSlot(int, int)
    def undoTransaction(self, coin: int, count: int) -> None:
        self._application.networkThread.undoTx.emit(
            self._application.coinList[coin],
            count)
