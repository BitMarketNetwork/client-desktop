from __future__ import annotations

from collections.abc import MutableSequence
from enum import Enum
from typing import TYPE_CHECKING

from PySide6.QtCore import Property as QProperty
from PySide6.QtCore import (
    QAbstractTableModel,
    QByteArray,
    QModelIndex,
    QObject,
    Qt,
)
from PySide6.QtCore import Signal as QSignal
from PySide6.QtCore import Slot as QSlot

if TYPE_CHECKING:
    from ....coins.abstract import CoinObject
    from ....database.tables import SerializableRowList
    from .. import QmlApplication


class AbstractCoinObjectModel(QObject if TYPE_CHECKING else object):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._list_model_list: dict[int, AbstractTableModel] = {}

    def _registerList(self, model: QObject):
        self._list_model_list[id(model)] = model
        return model

    @QSlot(QObject, result=None)
    def closeList(self, model: QObject) -> None:
        self._list_model_list.pop(id(model))

    def beforeInsertChild(
        self,
        object_: CoinObject,
        row_list: SerializableRowList,
        index: int,
    ) -> None:
        for m in self._list_model_list.values():
            if m.sourceList is row_list:
                m.lock(m.Lock.INSERT, index, 1)
                break
        super().beforeInsertChild(object_, row_list, index)

    def afterInsertChild(
        self,
        object_: CoinObject,
        row_list: SerializableRowList,
        index: int,
    ) -> None:
        for m in self._list_model_list.values():
            if m.sourceList is row_list:
                m.unlock()
                break
        super().afterInsertChild(object_, row_list, index)


class AbstractTableModel(QAbstractTableModel):
    __rowCountChanged = QSignal()

    class RoleEnum(Enum):
        MODEL = (Qt.UserRole + 1, QByteArray(b"modelObject"))

    class Lock(Enum):
        DUMMY = 0
        INSERT = 1
        REMOVE = 2
        RESET = 3

    def __init__(
        self,
        application: QmlApplication,
        source_list: MutableSequence[object],
        column_count: int = 1,
    ) -> None:
        super().__init__()
        self._application = application
        self._source_list = source_list
        self._column_count = column_count
        self.__lock = None

        self.rowsInserted.connect(self.__rowCountChanged)
        self.rowsRemoved.connect(self.__rowCountChanged)

    @property
    def sourceList(self) -> MutableSequence[object]:
        return self._source_list

    def roleNames(self) -> dict[Qt.ItemDataRole, QByteArray]:
        return {r.value[0]: r.value[1] for r in self.RoleEnum}

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._source_list)

    @QProperty(str, notify=__rowCountChanged)
    def rowCountHuman(self) -> str:
        return self._application.language.locale.integerToString(
            self.rowCount()
        )

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else self._column_count

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: Qt.ItemDataRole = Qt.DisplayRole,
    ) -> ...:
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return "column" + str(section)
            if orientation == Qt.Vertical:
                return "row" + str(section)
        return None

    def data(
        self,
        index: QModelIndex,
        role: Qt.ItemDataRole = Qt.DisplayRole,
    ) -> ...:
        if 0 <= index.row() < len(self._source_list) and index.isValid():
            if role == self.RoleEnum.MODEL.value[0]:
                return self._source_list[index.row()].model
        return None

    def lock(self, lock: Lock, first_index: int, count: int):
        assert self.__lock is None

        if lock == self.Lock.DUMMY:
            self.__lock = self.Lock.DUMMY
            return

        if lock == self.Lock.RESET:
            self.__lock = self.Lock.RESET
            self.beginResetModel()
            return

        if first_index < 0:
            first_index = self.rowCount()
        if count < 0:
            count = self.rowCount()

        last_index = first_index + count - 1

        if first_index > last_index:
            self.__lock = self.Lock.DUMMY
            return

        self.__lock = lock
        if lock == self.Lock.INSERT:
            self.beginInsertRows(QModelIndex(), first_index, last_index)
        elif lock == self.Lock.REMOVE:
            self.beginRemoveRows(QModelIndex(), first_index, last_index)
        else:
            raise AssertionError

    def unlock(self) -> None:
        assert self.__lock is not None
        if self.__lock == self.Lock.INSERT:
            self.endInsertRows()
        elif self.__lock == self.Lock.REMOVE:
            self.endRemoveRows()
        elif self.__lock == self.Lock.RESET:
            self.endResetModel()
        self.__lock = None
