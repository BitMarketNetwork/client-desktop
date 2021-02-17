# JOK++
from __future__ import annotations

from enum import Enum
from threading import Lock
from typing import TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal, \
    SignalInstance as QSignalInstance

if TYPE_CHECKING:
    from ..wallet.coins import CoinType
    from ..ui.gui import Application
    from ..language import Locale


class ValidStatus(Enum):
    Unset = 0
    Accept = 1
    Reject = 2


class AbstractStateModel(QObject):
    stateChanged = QSignal()

    def __init__(self, application: Application, coin: CoinType) -> None:
        super().__init__()
        self._application = application
        self._coin = coin

    def refresh(self) -> None:
        for a in dir(self):
            if a.endswith("__stateChanged"):
                a = getattr(self, a)
                if isinstance(a, QSignalInstance):
                    a.emit()
        self.stateChanged.emit()

    @property
    def locale(self) -> Locale:
        return self._application.language.locale

    def _getValidStatus(self) -> ValidStatus:
        return ValidStatus.Accept

    @QProperty(int, notify=stateChanged)
    def validStatus(self) -> int:
        return self._getValidStatus().value


class AbstractModel(QObject):
    stateChanged = QSignal()

    def __init__(self, application: Application) -> None:
        super().__init__()
        self._refresh_lock = Lock()
        self._application = application

    @property
    def locale(self) -> Locale:
        return self._application.language.locale

    def refresh(self, initiator: object) -> None:
        if self._refresh_lock.acquire(False):
            for a in dir(self):
                if not a.startswith("_"):
                    continue
                a = getattr(self, a)
                if not isinstance(a, AbstractStateModel):
                    continue
                if initiator is not a and hasattr(a, "refresh"):
                    a.refresh()
            self._refresh_lock.release()
            self.stateChanged.emit()
