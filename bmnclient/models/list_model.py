# JOK
from enum import Enum, unique

import PySide2.QtCore as QtCore


@unique
class DataRole(Enum):  # TODO IntEnum
    OBJECT = QtCore.Qt.UserRole + 1000


class ObjectListModel(QtCore.QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._list = []

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._list) if not parent.isValid() else 0

    def data(self, index, role=DataRole.OBJECT.value):
        if role != DataRole.OBJECT.value or not index.isValid():
            return None

        row = index.row()
        if row < 0 or row >= len(self._list):
            return None
        return self._list[row]

    def roleNames(self):
        return {
            DataRole.OBJECT.value: b'object'
        }

    def append(self, item):
        row = len(self._list)
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        self._list.append(item)
        self.endInsertRows()

    def remove(self):
        # TODO
        pass
