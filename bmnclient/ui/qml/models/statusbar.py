from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import (
    Property as QProperty,
    QObject,
    QTimer,
    Signal as QSignal)

if TYPE_CHECKING:
    from .. import QmlApplication


class StatusBar(QObject):
    stateChanged = QSignal()

    def __init__(self, application: QmlApplication) -> None:
        super().__init__()
        self._application = application
        self._isSync = False

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._update)

        self._timer.start()

    @QProperty(int, notify=stateChanged)
    def isSync(self) -> bool:
        return self._isSync

    def _update(self):
        if self._application.networkQueryManager.queueSize > 0:
            self._isSync = True
        else:
            self._isSync = False
        self.stateChanged.emit()
