
import logging
from typing import Optional, Union
from enum import auto
from . import \
    AbstractAddressStateModel, \
    AbstractAmountModel, \
    AbstractListModel, \
    AbstractListSortedModel, \
    RoleEnum

import PySide2.QtCore as qt_core  # pylint: disable=import-error
from ..models import RoleEnum
from ..wallet import tx  # pylint
log = logging.getLogger(__name__)


class TxListModel(AbstractListModel):
    class Role(RoleEnum):
        ID = auto()
        AMOUNT = auto()
        STATUS = auto()
        BLOCK = auto()
        HEIGHT = auto()
        TIME = auto()
        CREATED = auto()
        FEE = auto()
        CONFIRM = auto()
        INPUTS = auto()
        OUTPUTS = auto()


    _ROLE_MAP = {
        Role.ID: (
            b"name",
            lambda t: t.name),
        Role.AMOUNT: (
            b"balance",
            lambda t: t.balance),
        Role.STATUS: (
            b"status",
            lambda t: t.status),
        Role.BLOCK: (
            b"block",
            lambda t: t.block),
        Role.HEIGHT: (
            b"height",
            lambda t: t.height),
        Role.TIME: (
            b"timeHuman",
            lambda t: t.timeHuman),
        Role.CREATED: (
            b"TODO1",
            lambda t: t.time),
        Role.FEE: (
            b"feeHuman",
            lambda t: t.feeHuman),
        Role.CONFIRM: (
            b"confirmCount",
            lambda t: t.confirmCount),
        Role.INPUTS: (
            b"inputsModel",
            lambda t: t.inputsModel),
        Role.OUTPUTS: (
            b"outputsModel",
            lambda t: t.outputsModel)
    }

    def index_of(self, t) -> qt_core.QModelIndex:
        return self.index(self.address.index(t))


class TxProxyModel(qt_core.QSortFilterProxyModel):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.dynamicSortFilter = False
        # self.setSortRole(Role.HEIGHT)
        self.setSortRole(Role.CREATED)

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
        roles = [Role.CONFIRM, Role.STATUS, Role.BLOCK]
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
