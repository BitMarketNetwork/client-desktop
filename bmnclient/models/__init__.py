# JOK++
from enum import IntEnum
from functools import lru_cache
from typing import Any, List, Optional, Sequence

from PySide2.QtCore import \
    QAbstractListModel, \
    QByteArray, \
    QModelIndex, \
    QObject, \
    Qt, \
    Signal as QSignal


class RoleEnum(IntEnum):
    def _generate_next_value_(
            self,
            start: int,
            count: int,
            last_values: List[int]) -> int:
        return Qt.UserRole + count


class AbstractListModel(QAbstractListModel):
    _ROLE_MAP = {}

    def __init__(self, source_list: Sequence) -> None:
        super().__init__()
        self._source_list = source_list

    @lru_cache()
    def roleNames(self) -> dict:
        return {k: QByteArray(v[0]) for (k, v) in self._ROLE_MAP.items()}

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._source_list)

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> Any:
        if not 0 <= index.row() < self.rowCount() or not index.isValid():
            return None
        return self._ROLE_MAP[role][1](self._source_list[index.row()])


class AbstractStateModel(QObject):
    _stateChanged: Optional[QSignal] = None

    def refresh(self) -> None:
        if self._stateChanged:
            self._stateChanged.emit()
