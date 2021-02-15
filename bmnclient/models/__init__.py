# JOK++
from __future__ import annotations

from threading import Lock
from typing import Optional, TYPE_CHECKING

from PySide2.QtCore import \
    QObject, \
    Signal as QSignal

if TYPE_CHECKING:
    from ..wallet.coins import CoinType
    from ..ui.gui import Application
    from ..language import Locale


class AbstractStateModel(QObject):
    stateChanged: Optional[QSignal] = None

    def __init__(self, application: Application, coin: CoinType) -> None:
        super().__init__()
        self._application = application
        self._coin = coin

    def refresh(self) -> None:
        if self.stateChanged:
            self.stateChanged.emit()

    @property
    def locale(self) -> Locale:
        return self._application.language.locale


class AbstractModel(QObject):
    stateChanged: Optional[QSignal] = None

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
