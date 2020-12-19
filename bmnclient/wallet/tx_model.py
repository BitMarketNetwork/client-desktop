
import logging
import enum
from typing import Optional, Union

import PySide2.QtCore as qt_core  # pylint: disable=import-error

from .model_shared import IntEnum, ba
from ..wallet import tx  # pylint
log = logging.getLogger(__name__)


class Role(IntEnum):
    ID_ROLE = enum.auto()
    AMOUNT_ROLE = enum.auto()
    STATUS_ROLE = enum.auto()
    BLOCK_ROLE = enum.auto()
    HEIGHT_ROLE = enum.auto()
    TIME_ROLE = enum.auto()
    CREATED_ROLE = enum.auto()
    FEE_ROLE = enum.auto()
    CONFIRM_ROLE = enum.auto()
    INPUTS_ROLE = enum.auto()
    OUTPUTS_ROLE = enum.auto()


class TxModel(qt_core.QAbstractListModel):
    SELECTOR = {
        Role.ID_ROLE: lambda tx_: tx_.name,
        Role.AMOUNT_ROLE: lambda tx_: tx_.balance,
        Role.STATUS_ROLE: lambda tx_: tx_.status,
        Role.BLOCK_ROLE: lambda tx_: tx_.block,
        Role.HEIGHT_ROLE: lambda tx_: tx_.height,
        Role.TIME_ROLE: lambda tx_: tx_.timeHuman,
        Role.CREATED_ROLE: lambda tx_: tx_.time,
        Role.FEE_ROLE: lambda tx_: tx_.feeHuman,
        Role.CONFIRM_ROLE: lambda tx_: tx_.confirmCount,
        Role.INPUTS_ROLE: lambda tx_: tx_.inputsModel,
        Role.OUTPUTS_ROLE: lambda tx_: tx_.outputsModel,
    }

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.address = None

    def rowCount(self, parent=qt_core.QModelIndex()) -> int:
        if self.address:
            return len(self.address)
        return 0

    def data(self, index, role=qt_core.Qt.DisplayRole):
        if 0 <= index.row() < self.rowCount() and index.isValid():
            return self.SELECTOR[role](self.address[index.row()])

    def index_of(self, tx_) -> qt_core.QModelIndex:
        return self.index(self.address.index(tx_))

    def roleNames(self) -> dict:
        return {
            Role.ID_ROLE: ba(b"name"),
            Role.AMOUNT_ROLE: ba(b"balance"),
            Role.STATUS_ROLE: ba(b"status"),
            Role.BLOCK_ROLE: ba(b"block"),
            Role.TIME_ROLE: ba(b"timeHuman"),
            Role.FEE_ROLE: ba(b"feeHuman"),
            Role.CONFIRM_ROLE: ba(b"confirmCount"),
            Role.INPUTS_ROLE: ba(b"inputsModel"),
            Role.OUTPUTS_ROLE: ba(b"outputsModel"),
        }


class TxProxyModel(qt_core.QSortFilterProxyModel):

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.dynamicSortFilter = False
        # self.setSortRole(Role.HEIGHT_ROLE)
        self.setSortRole(Role.CREATED_ROLE)

    @property
    def address(self) -> 'address.CAddress':
        return self.sourceModel().address

    @qt_core.Property(bool)
    def empty(self) -> bool:
        return self.address is None

    def __sort(self) -> None:
        self.sort(0, order=qt_core.Qt.DescendingOrder)

    @address.setter
    def address(self, address: 'address.CAddress') -> None:
        assert address is not None
        self.beginResetModel()
        self.sourceModel().address = address
        self.endResetModel()
        self.__sort()

    def __test_address(self, address) -> bool:
        # log.debug(f"tx model test {address}. current:{self.address}")
        if self.address is not None and self.address.is_root:
                return address in self.address
        return self.address == address

    def append(self, address) -> None:
        if self.__test_address(address):
            self.sourceModel().beginInsertRows(qt_core.QModelIndex(), 0, 0)

    def append_list(self, address, count: int) -> None:
        if self.__test_address(address):
            log.debug(f"append {count} to {address}")
            self.sourceModel().beginInsertRows(qt_core.QModelIndex(), 0, count - 1)

    def append_complete(self, address):
        # log.debug(f"end append to  {address} ")
        if self.__test_address(address):
            self.sourceModel().endInsertRows()
            self.__sort()

    def remove_list(self, address, count: int) -> None:
        if self.__test_address(address):
            self.sourceModel().beginRemoveRows(qt_core.QModelIndex(), 0, count - 1)

    def remove_complete(self, address):
        if self.__test_address(address):
            self.sourceModel().endRemoveRows()
            self.__sort()

    def clear(self, address) -> None:
        if self.__test_address(address):
            self.sourceModel().beginRemoveRows(
                qt_core.QModelIndex(), 0, self.sourceModel().rowCount())

    def clear_complete(self, address) -> None:
        if self.__test_address(address):
            self.sourceModel().endRemoveRows()

    def update_confirm_count(self, tx_: Optional[Union[int, tx.Transaction]] = None) -> None:
        """
        tx_ is None - update #
        tx_ is int - update first
        tx_ is tx - update tx (doesnt work for a while)
        """
        roles = [Role.CONFIRM_ROLE, Role.STATUS_ROLE, Role.BLOCK_ROLE]
        if tx_:
            if isinstance(tx_, int):
                beg = self.index(0, 0)
                end = self.index(min(tx_, self.rowCount())-1, 0)
                self.dataChanged.emit(
                    beg, end, roles)
            else:
                index = self.mapFromSource(self.sourceModel().index_of(tx_))
                self.dataChanged.emit(
                    index, index, roles)
        else:
            beg = self.index(0, 0)
            end = self.index(self.rowCount()-1, 0)
            self.dataChanged.emit(
                beg, end, roles)
