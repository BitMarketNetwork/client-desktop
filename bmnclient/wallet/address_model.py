import enum
import logging

import PySide2.QtCore as qt_core  # pylint: disable=import-error
from .model_shared import IntEnum, ba
log = logging.getLogger(__name__)


class Role(IntEnum):
    NAME_ROLE = enum.auto()
    LABEL_ROLE = enum.auto()
    BALANCE_ROLE = enum.auto()
    EMPTY_BALANCE_ROLE = enum.auto()
    FIAT_BALANCE_ROLE = enum.auto()
    TIME_ROLE = enum.auto()
    READONLY_ROLE = enum.auto()
    UPDATING_ROLE = enum.auto()


class AddressModel(qt_core.QAbstractListModel):
    SELECTOR = {
        Role.NAME_ROLE: lambda add_: add_.name,
        Role.LABEL_ROLE: lambda add_: add_.label,
        Role.BALANCE_ROLE: lambda add_: add_.balance,
        Role.EMPTY_BALANCE_ROLE: lambda add_: add_.empty_balance,
        Role.FIAT_BALANCE_ROLE: lambda add_: add_.fiatBalance,
        Role.TIME_ROLE: lambda add_: add_.created_db_repr,
        Role.READONLY_ROLE: lambda add_: add_.readOnly,
        Role.UPDATING_ROLE: lambda add_: add_.isUpdating,
    }

    def __init__(self, coin):
        super().__init__(parent=coin)
        self.__coin = coin

    def rowCount(self, parent=qt_core.QModelIndex()):
        return len(self.__coin)

    @property
    def coin(self) -> "CoinBase":
        return self.__coin

    def data(self, index, role=qt_core.Qt.DisplayRole):
        if 0 <= index.row() < self.rowCount() and index.isValid():
            try:
                return self.SELECTOR[role](self.__coin[index.row()])
            except KeyError as ke:
                log.critical(f"{ke} ==> role:{role} row:{index.row()}")

    def index_of(self, address) -> qt_core.QModelIndex:
        return self.index(self.__coin.index(address))

    def roleNames(self):
        return {
            Role.NAME_ROLE: ba(b"name"),
            Role.LABEL_ROLE: ba(b"label"),
            Role.BALANCE_ROLE: ba(b"balance"),
            Role.FIAT_BALANCE_ROLE: ba(b"fiatBalance"),
            Role.READONLY_ROLE: ba(b"readOnly"),
            Role.UPDATING_ROLE: ba(b"isUpdating"),
        }


class AddressProxyModel(qt_core.QSortFilterProxyModel):
    updated = qt_core.Signal()

    def __init__(self, parent):
        super().__init__(parent=parent)
        self._empty_filter = False
        # TODO: later
        self.dynamicSortFilter = False
        self.setSortRole(Role.BALANCE_ROLE)

    def __sort(self) -> None:
        self.sort(0, order=qt_core.Qt.DescendingOrder)

    @qt_core.Property(bool, notify=updated)
    def emptyFilter(self) -> bool:
        return self._empty_filter

    @emptyFilter.setter
    def _set_empty_filter(self, val: bool) -> None:
        self._empty_filter = val
        self.invalidate()

    def filterAcceptsRow(self, source_row, source_parent) -> bool:
        if not self._empty_filter:
            return True
        return not self.sourceModel().data(self.sourceModel().index(source_row, 0, source_parent), Role.EMPTY_BALANCE_ROLE)

    def __call__(self, idx: int) -> "address.CAddress":
        return self.sourceModel().coin[self.mapToSource(self.index(idx, 0)).row()]

    def append(self) -> None:
        self.beginInsertRows(qt_core.QModelIndex(),
                             self.rowCount(), self.rowCount())

    def append_complete(self) -> None:
        self.endInsertRows()
        self.invalidate()
        self.__sort()
        # log.warning("need to update coin cell")

    def remove(self, index: int) -> None:
        index = self.mapFromSource(self.sourceModel().index(index)).row()
        self.beginRemoveRows(qt_core.QModelIndex(),
                             index, index)

    def remove_complete(self) -> None:
        self.endRemoveRows()
        self.invalidate()
        self.__sort()

    def reset(self) -> None:
        self.beginResetModel()
        self.endResetModel()
        self.invalidate()
        self.__sort()

    def address_updated(self, address):
        index = self.mapFromSource(self.sourceModel().index_of(address))
        # readonly important when we load key
        self.dataChanged.emit(index, index, [Role.UPDATING_ROLE , Role.READONLY_ROLE ])

    def balance_changed(self, address):
        index = self.mapFromSource(self.sourceModel().index_of(address))
        self.dataChanged.emit(index, index, [Role.READONLY_ROLE , Role.BALANCE_ROLE, Role.FIAT_BALANCE_ROLE])
        self.invalidate()
        self.__sort()
