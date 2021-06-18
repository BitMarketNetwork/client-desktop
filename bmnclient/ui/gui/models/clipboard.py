# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal
from PySide2.QtGui import QClipboard

if TYPE_CHECKING:
    from .. import GuiApplication


class ClipboardModel(QObject):
    _MODE = QClipboard.Clipboard
    stateChanged = QSignal()

    def __init__(self, application: GuiApplication) -> None:
        super().__init__()
        self._application = application
        # noinspection PyUnresolvedReferences
        self._application.clipboard.changed.connect(self._onChanged)

    @QProperty(str, notify=stateChanged)
    def text(self) -> str:
        return self._application.clipboard.text("plain", self._MODE)

    @text.setter
    def _setText(self, value: str):
        self._application.clipboard.setText(value, self._MODE)

    def _onChanged(self, mode: QClipboard.Mode):
        if mode == self._MODE:
            # noinspection PyUnresolvedReferences
            self.stateChanged.emit()
