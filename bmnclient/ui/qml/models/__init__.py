from __future__ import annotations

from enum import IntEnum
from threading import Lock
from typing import Final, Generator, TYPE_CHECKING

from PySide6.QtCore import (
    Property as QProperty,
    QObject,
    Signal as QSignal,
    SignalInstance as QSignalInstance,
    Slot as QSlot)

if TYPE_CHECKING:
    from .abstract import AbstractTableModel
    from .. import QmlApplication
    from ....coins.abstract import Coin
    from ....config import ConfigKey
    from ....language import Locale

# TODO move all to .abstract


class ValidStatus(IntEnum):
    Unset = 0
    Reject = 1
    Accept = 2


class AbstractStateModel(QObject):
    _NONE_STRING: Final = "-"
    stateChanged = QSignal()

    def __init__(self, application: QmlApplication) -> None:
        super().__init__()
        self._application = application

    def update(self) -> None:
        for a in dir(self):
            if a.endswith("__stateChanged"):
                a = getattr(self, a)
                if isinstance(a, QSignalInstance):
                    a.emit()
        # noinspection PyUnresolvedReferences
        self.stateChanged.emit()

    @property
    def locale(self) -> Locale:
        return self._application.language.locale

    def _getValidStatus(self) -> ValidStatus:
        return ValidStatus.Accept

    @QProperty(int, notify=stateChanged)
    def validStatus(self) -> ValidStatus:
        return self._getValidStatus()

    @QProperty(bool, notify=stateChanged)
    def isValid(self) -> bool:
        return self._getValidStatus() == ValidStatus.Accept


class AbstractTupleStateModel(AbstractStateModel):
    __stateChanged = QSignal()

    def __init__(
            self,
            application: QmlApplication,
            source_list: tuple[dict[str, ...], ...],
            *,
            config_key: ConfigKey | None = None,
            default_name: str | None = None) -> None:
        super().__init__(application)
        self._list = source_list
        self._config_key = config_key
        self.__default_name = default_name

        if self._config_key is not None:
            self.__current_name = self._application.config.get(
                self._config_key,
                str,
                "")
            if self.__default_name is not None:
                if not self._isValidName(self.__current_name):
                    self.__current_name = self.__default_name
        else:
            self.__current_name = None

    @QProperty(list, constant=True)
    def list(self) -> tuple:
        return self._list

    @QProperty(str, constant=True)
    def defaultName(self) -> str:
        return self.__default_name

    @QProperty(str, notify=__stateChanged)
    def currentName(self) -> str:
        return self._getCurrentItemName()

    @currentName.setter
    def currentName(self, value: str) -> None:
        if not self._isValidName(value):
            return
        if self._getCurrentItemName() != value:
            if self._setCurrentItemName(value):
                self.update()

    def _isValidName(self, name) -> bool:
        return bool(name and any(name == v["name"] for v in self._list))

    def _getCurrentItemName(self) -> str:
        if self.__current_name is None:
            raise NotImplementedError
        return self.__current_name

    def _setCurrentItemName(self, value: str) -> bool:
        if self._config_key is None:
            raise NotImplementedError
        self._application.config.set(self._config_key, value)
        self.__current_name = value
        return True


class AbstractCoinStateModel(AbstractStateModel):
    def __init__(self, application: QmlApplication, coin: Coin) -> None:
        super().__init__(application)
        self._coin = coin


class AbstractModel(QObject):
    stateChanged = QSignal()

    def __init__(self, application: QmlApplication, *args, **kwargs) -> None:
        assert not kwargs
        assert not args
        super().__init__()
        self._application = application
        self._update_lock = Lock()
        self._list_model_list: dict[int, AbstractTableModel] = {}

    def _registerList(self, model: QObject):
        self._list_model_list[id(model)] = model
        return model

    @QSlot(QObject, result=None)
    def closeList(self, model: QObject) -> None:
        self._list_model_list.pop(id(model))

    def iterateStateModels(self) -> Generator[AbstractStateModel, None, None]:
        for a in dir(self):
            if a.startswith("_"):
                a = getattr(self, a)
                if isinstance(a, AbstractStateModel):
                    yield a

    @property
    def locale(self) -> Locale:
        return self._application.language.locale

    # TODO check usage
    def update(self, initiator: QObject | None = None) -> None:
        if self._update_lock.acquire(False):
            for a in self.iterateStateModels():
                if a is not initiator:
                    a.update()
            self._update_lock.release()
            # noinspection PyUnresolvedReferences
            self.stateChanged.emit()

    def connectModelUpdate(self, model: QObject) -> None:
        model.stateChanged.connect(lambda: self.update(model))

    # TODO check usage
    @QProperty(int, notify=stateChanged)
    def validStatus(self) -> ValidStatus:
        result = ValidStatus.Accept
        for a in self.iterateStateModels():
            a = a.validStatus
            # noinspection PyTypeChecker
            if int(a) < int(result):
                result = a
        if result == ValidStatus.Unset:
            result = ValidStatus.Reject
        return result

    @QProperty(bool, notify=stateChanged)
    def isValid(self) -> bool:
        return self.validStatus == ValidStatus.Accept
