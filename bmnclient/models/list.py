# JOK+++
from __future__ import annotations

from enum import IntEnum
from functools import lru_cache
from typing import TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QAbstractListModel, \
    QByteArray, \
    QConcatenateTablesProxyModel, \
    QModelIndex, \
    QSortFilterProxyModel, \
    Qt, \
    Signal as QSignal

if TYPE_CHECKING:
    from typing import Any, List, Optional, Sequence
    from ..ui.gui import Application


class RoleEnum(IntEnum):
    def _generate_next_value_(
            self,
            start: int,
            count: int,
            last_values: List[int]) -> int:
        return Qt.UserRole + count


class ListModelHelper:
    __rowCountChanged = QSignal()

    def __init__(self, application: Application) -> None:
        self._application = application
        # noinspection PyUnresolvedReferences
        self.rowsInserted.connect(lambda **_: self.__rowCountChanged.emit())
        # noinspection PyUnresolvedReferences
        self.rowsRemoved.connect(lambda **_: self.__rowCountChanged.emit())

    @QProperty(str, notify=__rowCountChanged)
    def rowCountHuman(self) -> str:
        # noinspection PyUnresolvedReferences
        return self._application.language.locale.integerToString(
            self.rowCount())


class AbstractListModel(QAbstractListModel, ListModelHelper):
    class _LockRows:
        def __init__(
                self,
                owner: AbstractListModel,
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

        def __exit__(self, exc_type, exc_value, traceback) -> None:
            raise NotImplementedError

    class LockInsertRows(_LockRows):
        def __enter__(self) -> None:
            if not self._dummy:
                self._owner.beginInsertRows(
                    QModelIndex(),
                    self._first_index,
                    self._last_index)

        def __exit__(self, exc_type, exc_value, traceback) -> None:
            if not self._dummy:
                self._owner.endInsertRows()

    class LockRemoveRows(_LockRows):
        def __enter__(self) -> None:
            if not self._dummy:
                self._owner.beginRemoveRows(
                    QModelIndex(),
                    self._first_index,
                    self._last_index)

        def __exit__(self, exc_type, exc_value, traceback) -> None:
            if not self._dummy:
                self._owner.endRemoveRows()

    class LockReset:
        def __init__(self, owner: AbstractListModel) -> None:
            self._owner = owner

        def __enter__(self) -> None:
            self._owner.beginResetModel()

        def __exit__(self, exc_type, exc_value, traceback) -> None:
            self._owner.endResetModel()

    ROLE_MAP = {}

    def __init__(self, application: Application, source_list: Sequence) -> None:
        super().__init__()
        ListModelHelper.__init__(self, application)
        self._source_list = source_list
        self._data_list: List[dict] = [{}] * len(self._source_list)
        self.__lock = None

    def _getRoleValue(self, index: QModelIndex, role) -> Optional[dict]:
        if not 0 <= index.row() < self.rowCount() or not index.isValid():
            return None
        return self.ROLE_MAP.get(role, None)

    @lru_cache()
    def roleNames(self) -> dict:
        return {k: QByteArray(v[0]) for (k, v) in self.ROLE_MAP.items()}

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._source_list)

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> Any:
        role_value = self._getRoleValue(index, role)
        if role_value is None:
            return None
        if isinstance(role_value[1], str):
            return self._data_list[index.row()].get(role_value[1], None)
        else:
            return role_value[1](self._source_list[index.row()])

    def setData(self, index: QModelIndex, value: Any, role=Qt.EditRole) -> bool:
        role_value = self._getRoleValue(index, role)
        if role_value is None or not isinstance(role_value[1], str):
            return False
        self._data_list[index.row()][role_value[1]] = value
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

    def beginMoveRows(
            self,
            source_parent: QModelIndex,
            source_first_index: int,
            source_last_index: int,
            destination_parent: QModelIndex,
            destination_child_index: int) -> bool:
        return False

    def beginRemoveRows(
            self,
            parent: QModelIndex,
            first_index: int,
            last_index: int) -> None:
        super().beginRemoveRows(parent, first_index, last_index)
        while range(first_index, last_index + 1):
            self._data_list.pop(first_index)

    def endResetModel(self) -> None:
        self._data_list = [{}] * len(self._source_list)
        super().endResetModel()

    def lockInsertRows(self, first_index=-1, count=1) -> LockInsertRows:
        return self.LockInsertRows(self, first_index, count)

    def lockRemoveRows(self, first_index=0, count=-1) -> LockRemoveRows:
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


class AbstractConcatenateModel(QConcatenateTablesProxyModel, ListModelHelper):
    ROLE_MAP = {}

    def __init__(self, application: Application) -> None:
        super().__init__()
        ListModelHelper.__init__(self, application)

    @lru_cache()
    def roleNames(self) -> dict:
        return {k: QByteArray(v[0]) for (k, v) in self.ROLE_MAP.items()}


class AbstractListSortedModel(QSortFilterProxyModel, ListModelHelper):
    def __init__(
            self,
            application: Application,
            source_model: AbstractListModel,
            sort_role: int,
            sort_order=Qt.AscendingOrder) -> None:
        super().__init__()
        ListModelHelper.__init__(self, application)
        self.setSourceModel(source_model)
        self.setSortRole(sort_role)
        self.sort(0, sort_order)
