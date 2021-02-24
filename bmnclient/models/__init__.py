# JOK++
from __future__ import annotations

from enum import IntEnum
from threading import Lock
from typing import Iterable, Optional, TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal, \
    SignalInstance as QSignalInstance

if TYPE_CHECKING:
    from ..wallet.coins import CoinType
    from ..ui.gui import Application
    from ..language import Locale


class ValidStatus(IntEnum):
    Unset = 0
    Reject = 1
    Accept = 2


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

    # noinspection PyMethodMayBeStatic
    def _getValidStatus(self) -> ValidStatus:
        return ValidStatus.Accept

    @QProperty(int, notify=stateChanged)
    def validStatus(self) -> ValidStatus:
        return self._getValidStatus()

    @QProperty(bool, notify=stateChanged)
    def isValid(self) -> bool:
        return self._getValidStatus() == ValidStatus.Accept


class AbstractModel(QObject):
    stateChanged = QSignal()

    def __init__(self, application: Application) -> None:
        super().__init__()
        self._refresh_lock = Lock()
        self._application = application

    def iterateStateModels(self) -> Iterable[AbstractStateModel]:
        for a in dir(self):
            if a.startswith("_"):
                a = getattr(self, a)
                if isinstance(a, AbstractStateModel):
                    yield a

    @property
    def locale(self) -> Locale:
        return self._application.language.locale

    # TODO check usage
    def refresh(self, initiator: Optional[QObject] = None) -> None:
        if self._refresh_lock.acquire(False):
            for a in self.iterateStateModels():
                if a is not initiator:
                    a.refresh()
            self._refresh_lock.release()
            self.stateChanged.emit()

    def connectModelRefresh(self, model: QObject) -> None:
        model.stateChanged.connect(lambda: self.refresh(model))

    # TODO check usage
    @QProperty(int, notify=stateChanged)
    def validStatus(self) -> ValidStatus:
        result = ValidStatus.Accept
        for a in self.iterateStateModels():
            a = a.validStatus
            if a < result:
                result = a
        if result == ValidStatus.Unset:
            result = ValidStatus.Reject
        return result

    @QProperty(bool, notify=stateChanged)
    def isValid(self) -> bool:
        return self.validStatus == ValidStatus.Accept
