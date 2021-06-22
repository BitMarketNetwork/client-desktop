# JOK TODO
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PySide2.QtCore import \
    QObject, \
    Slot as QSlot

if TYPE_CHECKING:
    from . import GuiApplication


class DebugManager(QObject):
    def __init__(self, application: GuiApplication):
        super().__init__()
        self._application = application

    @QSlot(int)
    def increaseHeight(self, value: int) -> None:
        for coin in self._application.coinList:
            coin.height += value

    @QSlot(int)
    def kill(self, signal: int) -> None:
        os.kill(os.getpid(), signal)

    @QSlot(int, int)
    def undoTransaction(self, coin: int, count: int) -> None:
        # TODO
        pass
