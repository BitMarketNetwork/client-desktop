from __future__ import annotations

import logging
from typing import Optional, Union, TYPE_CHECKING
from enum import auto
from . import \
    AbstractAmountModel, \
    AbstractListModel, \
    AbstractListSortedModel, \
    AbstractTxStateModel, \
    RoleEnum

from PySide2.QtCore import \
    Property as QProperty, \
    QDateTime, \
    QLocale, \
    Signal as QSignal

import PySide2.QtCore as qt_core  # pylint: disable=import-error
if TYPE_CHECKING:
    from ..wallet import tx  # pylint

log = logging.getLogger(__name__)


class TxStateModel(AbstractTxStateModel):
    _stateChanged = QSignal()

    @QProperty(int, notify=_stateChanged)
    def status(self) -> int:
        return self._tx.status

    @QProperty(str, notify=_stateChanged)
    def timeHuman(self) -> str:
        v = QDateTime()
        v.setSecsSinceEpoch(self._tx.time)
        return self._application.language.locale.toString(
            v,
            QLocale.LongFormat)

    @QProperty(int, notify=_stateChanged)
    def height(self) -> int:
        return self._tx.height

    @QProperty(int, notify=_stateChanged)
    def confirmations(self) -> int:
        return self._tx.confirmCount


class TxAmountModel(AbstractAmountModel, AbstractTxStateModel):
    def _value(self) -> int:
        return self._tx.balance

    def _fiatValue(self) -> float:
        return self._tx.fiatBalance


class TxFeeAmountModel(AbstractAmountModel, AbstractTxStateModel):
    def _value(self) -> int:
        return self._tx.fee

    def _fiatValue(self) -> float:
        return self._tx.feeFiatBalance


class TxListModel(AbstractListModel):
    class Role(RoleEnum):
        NAME = auto()
        AMOUNT = auto()
        FEE_AMOUNT = auto()
        STATE = auto()
        INPUT_LIST = auto()
        OUTPUT_LIST = auto()

    _ROLE_MAP = {
        Role.NAME: (
            b"name",
            lambda t: t.name),
        Role.AMOUNT: (
            b"amount",
            lambda t: t.amountModel),
        Role.FEE_AMOUNT: (
            b"feeAmount",
            lambda t: t.feeAmountModel),
        Role.STATE: (
            b"state",
            lambda t: t.stateModel),
        Role.INPUT_LIST: (
            b"inputList",
            lambda t: t.inputsModel),
        Role.OUTPUT_LIST: (
            b"outputList",
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
