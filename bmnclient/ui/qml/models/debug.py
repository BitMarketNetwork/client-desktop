# JOK4
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PySide2.QtCore import \
    QObject, \
    Slot as QSlot

if TYPE_CHECKING:
    from . import QmlApplication


class DebugManager(QObject):
    def __init__(self, application: QmlApplication):
        super().__init__()
        self._application = application

    @QSlot(int)
    def increaseHeight(self, value: int) -> None:
        for coin in self._application.coinList:
            coin.height += value

    @QSlot(int)
    def kill(self, signal: int) -> None:
        os.kill(os.getpid(), signal)

    @QSlot(str, str)
    def notify(self, message: str, icon: str) -> None:
        if icon == "n":
            icon = self._application.systemTrayIcon.MessageIcon.NONE
        elif icon == "i":
            icon = self._application.systemTrayIcon.MessageIcon.INFORMATION
        elif icon == "w":
            icon = self._application.systemTrayIcon.MessageIcon.WARNING
        elif icon == "e":
            icon = self._application.systemTrayIcon.MessageIcon.ERROR
        else:
            icon = self._application.systemTrayIcon.MessageIcon.INFORMATION
        self._application.systemTrayIcon.showMessage(message, icon)
