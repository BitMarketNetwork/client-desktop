from __future__ import annotations
from csv import list_dialects

from enum import IntEnum
from typing import TYPE_CHECKING

from PySide6.QtCore import (
    Property as QProperty,
    QAbstractItemModel,
    QAbstractListModel,
    QAbstractTableModel,
    QByteArray,
    QConcatenateTablesProxyModel,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
    Signal as QSignal)

if TYPE_CHECKING:
    from typing import Any, List, Optional, Sequence
    from .. import QmlApplication


class RoleEnum(IntEnum):
    def _generate_next_value_(
            self,
            start: int,
            count: int,
            last_values: List[int]) -> int:
        return Qt.UserRole + count


class AbstractModel(QAbstractItemModel if TYPE_CHECKING else object):
    __rowCountChanged = QSignal()

    def __init__(self, application: QmlApplication) -> None:
        super().__init__()
        self._application = application
        # noinspection PyUnresolvedReferences
        self.rowsInserted.connect(lambda *_: self.__rowCountChanged.emit())
        # noinspection PyUnresolvedReferences
        self.rowsRemoved.connect(lambda *_: self.__rowCountChanged.emit())

    @QProperty(str, notify=__rowCountChanged)
    def rowCountHuman(self) -> str:
        return self._application.language.locale.integerToString(
            self.rowCount())


class AbstractItemModel(AbstractModel):
    class _LockRows:
        def __init__(
                self,
                owner: QAbstractItemModel,
                first_index: int,
                count: int) -> None:
            if first_index < 0:
                first_index = owner.rowCount()
            if count < 0:
                count = owner.rowCount()

            self._owner = owner
            self._first_index = first_index
            self._last_index = first_index + count - 1
            self._dummy = self._first_index > self._last_index

        def __enter__(self) -> None:
            raise NotImplementedError

        def __exit__(self, exc_type, exc_value, traceback) -> bool:
            raise NotImplementedError

    class LockInsertRows(_LockRows):
        def __enter__(self) -> None:
            if not self._dummy:
                self._owner.beginInsertRows(
                    QModelIndex(),
                    self._first_index,
                    self._last_index)

        def __exit__(self, exc_type, exc_value, traceback) -> bool:
            if not self._dummy:
                self._owner.endInsertRows()
            return False

    class LockRemoveRows(_LockRows):
        def __enter__(self) -> None:
            if not self._dummy:
                self._owner.beginRemoveRows(
                    QModelIndex(),
                    self._first_index,
                    self._last_index)

        def __exit__(self, exc_type, exc_value, traceback) -> bool:
            if not self._dummy:
                self._owner.endRemoveRows()
            return False

    class LockReset:
        def __init__(self, owner: QAbstractItemModel) -> None:
            self._owner = owner

        def __enter__(self) -> None:
            self._owner.beginResetModel()

        def __exit__(self, exc_type, exc_value, traceback) -> bool:
            self._owner.endResetModel()
            return False

    _ROLE_MAP = {}
    _COLUMN_COUNT = 1

    def __init__(
            self,
            application: QmlApplication,
            source_list: Sequence) -> None:
        super().__init__(application)
        self._source_list = source_list
        self._data_list: List[dict] = [{}] * len(self._source_list)
        self.__lock = None

    def _getRoleValue(self, index: QModelIndex, role) -> Optional[dict]:
        if not 0 <= index.row() < self.rowCount() or not index.isValid():
            return None
        return self._ROLE_MAP.get(role, None)

    def roleNames(self) -> dict:
        return {k: QByteArray(v[0]) for (k, v) in self._ROLE_MAP.items()}

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._source_list)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return self._COLUMN_COUNT

    # noinspection PyMethodMayBeStatic
    def headerData(
            self,
            section: int,
            orientation: Qt.Orientation,
            role: Qt.ItemDataRole = Qt.DisplayRole) -> Any:
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return "column" + str(section)
            if orientation == Qt.Vertical:
                return "row" + str(section)
        return None

    def data(
            self,
            index: QModelIndex,
            role: Qt.ItemDataRole = Qt.DisplayRole) -> Any:
        role_value = self._getRoleValue(index, role)
        if role_value is None:
            return None
        if isinstance(role_value[1], str):
            return self._data_list[index.row()].get(role_value[1])
        else:
            return role_value[1](self._source_list[index.row()])

    def setData(
            self,
            index: QModelIndex,
            value: Any,
            role: Qt.ItemDataRole = Qt.EditRole) -> bool:
        role_value = self._getRoleValue(index, role)
        if role_value is None or not isinstance(role_value[1], str):
            return False
        data = self._data_list[index.row()]
        data_name = role_value[1]
        if data.setdefault(data_name) != value:
            data[data_name] = value
            if not data_name.startswith("_"):
                self.dataChanged.emit(index, index, [role])
        return True

    def beginInsertRows(
            self,
            parent: QModelIndex,
            first_index: int,
            last_index: int) -> None:
        super().beginInsertRows(parent, first_index, last_index)
        for i in range(first_index, last_index + 1):
            self._data_list.insert(i, {})

    def beginRemoveRows(
            self,
            parent: QModelIndex,
            first_index: int,
            last_index: int) -> None:
        super().beginRemoveRows(parent, first_index, last_index)
        #while range(first_index, last_index + 1):
        #    self._data_list.pop(first_index)
        self._source_list = self._source_list[:first_index] + self._source_list[last_index + 1:]
        self._data_list = [{}] * len(self._source_list)

    def endResetModel(self) -> None:
        self._data_list = [{}] * len(self._source_list)
        super().endResetModel()

    def lockInsertRows(
            self,
            first_index: int = -1,
            count: int = 1) -> LockInsertRows:
        return self.LockInsertRows(self, first_index, count)

    def lockRemoveRows(
            self,
            first_index: int = 0,
            count: int = -1) -> LockRemoveRows:
        return self.LockRemoveRows(self, first_index, count)

    def lockReset(self) -> LockReset:
        return self.LockReset(self)

    def lock(self, lock: _LockRows):
        assert self.__lock is None
        self.__lock = lock
        self.__lock.__enter__()

    def unlock(self) -> None:
        assert self.__lock is not None
        self.__lock.__exit__(None, None, None)
        self.__lock = None


class AbstractProxyModel(AbstractModel):
    pass


class AbstractListModel(AbstractItemModel, QAbstractListModel):
    pass


class AbstractTableModel(AbstractItemModel, QAbstractTableModel):
    pass


class AbstractConcatenateModel(
        AbstractProxyModel,
        QConcatenateTablesProxyModel):
    def roleNames(self) -> dict:
        return {k: QByteArray(v[0]) for (k, v) in self._ROLE_MAP.items()}


class AbstractSortedModel(AbstractProxyModel, QSortFilterProxyModel):
    def __init__(
            self,
            application: QmlApplication,
            source_model: AbstractListModel,
            sort_role: int,
            sort_order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        super().__init__(application)

        # TODO self.setDynamicSortFilter(False)
        self.setSourceModel(source_model)
        self.setSortRole(sort_role)
        self.sort(0, sort_order)
