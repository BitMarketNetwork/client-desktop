from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PySide6.QtCore import Property as QProperty
from PySide6.QtCore import QObject
from PySide6.QtCore import Slot as QSlot

from ....debug import Debug

if TYPE_CHECKING:
    from . import QmlApplication


class DebugModel(QObject):
    def __init__(self, application: QmlApplication):
        super().__init__()
        self._application = application

    @QProperty(bool, constant=True)
    def isEnabled(self) -> bool:
        return Debug.isEnabled

    @QSlot(int)
    def increaseHeight(self, value: int) -> None:
        for coin in self._application.coinList:
            coin.height += value

    @QSlot(int)
    def kill(self, signal: int) -> None:
        os.kill(os.getpid(), signal)

    @QSlot(str, str)
    def showMessage(self, type_: str, text: str) -> None:
        if type_ == "i":
            type_ = self._application.MessageType.INFORMATION
        elif type_ == "w":
            type_ = self._application.MessageType.WARNING
        elif type_ == "e":
            type_ = self._application.MessageType.ERROR
        else:
            type_ = self._application.MessageType.INFORMATION

        self._application.showMessage(
            type_=type_, title="showMessage() Test", text=text
        )
