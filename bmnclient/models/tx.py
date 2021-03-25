# JOK++
from __future__ import annotations

from abc import ABCMeta
from enum import auto
from typing import Optional, TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QDateTime, \
    QModelIndex, \
    QObject, \
    Qt, \
    Signal as QSignal

from . import AbstractModel, AbstractStateModel
from .address import AddressListModel
from .amount import AmountModel
from .list import \
    AbstractConcatenateModel, \
    AbstractListModel, \
    AbstractListSortedModel, \
    RoleEnum
from ..coins.tx import TxModelInterface

if TYPE_CHECKING:
    from typing import Final
    from ..ui.gui import Application
    from ..coins.tx import AbstractTx


class AbstractTxStateModel(AbstractStateModel):
    def __init__(self, application: Application, tx: AbstractTx) -> None:
        super().__init__(application, tx.address.coin)
        self._tx = tx


class AbstractTxAmountModel(AmountModel, metaclass=ABCMeta):
    def __init__(self, application: Application, tx: AbstractTx) -> None:
        super().__init__(application, tx.address.coin)
        self._tx = tx


class TxStateModel(AbstractTxStateModel):
    __stateChanged = QSignal()

    @QProperty(int, notify=__stateChanged)
    def status(self) -> int:
        return self._tx.status.value

    @QProperty(int, notify=__stateChanged)
    def time(self) -> int:
        return self._tx.time

    @QProperty(str, notify=__stateChanged)
    def timeHuman(self) -> str:
        v = QDateTime()
        v.setSecsSinceEpoch(self._tx.time)
        return self.locale.toString(v, self.locale.LongFormat)

    @QProperty(int, notify=__stateChanged)
    def height(self) -> int:
        return self._tx.height

    @QProperty(str, notify=__stateChanged)
    def heightHuman(self) -> str:
        if self._tx.height < 0:
            return "-"
        return self.locale.integerToString(self._tx.height)

    @QProperty(int, notify=__stateChanged)
    def confirmations(self) -> int:
        return self._tx.confirmations

    @QProperty(str, notify=__stateChanged)
    def confirmationsHuman(self) -> str:
        return self.locale.integerToString(self._tx.confirmations)


class TxAmountModel(AbstractTxAmountModel):
    def refresh(self) -> None:
        super().refresh()
        for address in self._tx.inputList:
            address.model.amount.refresh()
        for address in self._tx.outputList:
            address.model.amount.refresh()

    def _getValue(self) -> Optional[int]:
        return self._tx.amount


class TxFeeAmountModel(AbstractTxAmountModel):
    def _getValue(self) -> Optional[int]:
        return self._tx.fee


class TxModel(TxModelInterface, AbstractModel):
    def __init__(self, application: Application, tx: AbstractTx) -> None:
        super().__init__(application)
        self._tx = tx

        self._amount_model = TxAmountModel(
            self._application,
            self._tx)
        self.connectModelRefresh(self._amount_model)

        self._fee_amount_model = TxFeeAmountModel(
            self._application,
            self._tx)
        self.connectModelRefresh(self._fee_amount_model)

        self._state_model = TxStateModel(
            self._application,
            self._tx)
        self.connectModelRefresh(self._state_model)

        self._input_list_model = TxIoListModel(
            self._application,
            self._tx.inputList)
        self._output_list_model = TxIoListModel(
            self._application,
            self._tx.outputList)

    @QProperty(str, constant=True)
    def name(self) -> str:
        return self._tx.name

    @QProperty(QObject, constant=True)
    def amount(self) -> TxAmountModel:
        return self._amount_model

    @QProperty(QObject, constant=True)
    def feeAmount(self) -> TxFeeAmountModel:
        return self._fee_amount_model

    @QProperty(QObject, constant=True)
    def state(self) -> TxStateModel:
        return self._state_model

    @QProperty(QObject, constant=True)
    def inputList(self) -> TxIoListModel:
        return self._input_list_model

    @QProperty(QObject, constant=True)
    def outputList(self) -> TxIoListModel:
        return self._output_list_model

    def afterSetHeight(self) -> None:
        self._state_model.refresh()

    def afterSetTime(self) -> None:
        self._state_model.refresh()


class TxIoListModel(AddressListModel):
    pass


class TxListModel(AbstractListModel):
    class Role(RoleEnum):
        INSTANCE: Final = auto()
        NAME: Final = auto()
        AMOUNT: Final = auto()
        FEE_AMOUNT: Final = auto()
        STATE: Final = auto()
        INPUT_LIST: Final = auto()
        OUTPUT_LIST: Final = auto()

    ROLE_MAP: Final = {
        Role.INSTANCE: (
            b"_instance",
            lambda t: t),
        Role.NAME: (
            b"name",
            lambda t: t.model.name),
        Role.AMOUNT: (
            b"amount",
            lambda t: t.model.amount),
        Role.FEE_AMOUNT: (
            b"feeAmount",
            lambda t: t.model.feeAmount),
        Role.STATE: (
            b"state",
            lambda t: t.model.state),
        Role.INPUT_LIST: (
            b"inputList",
            lambda t: t.model.inputList),
        Role.OUTPUT_LIST: (
            b"outputList",
            lambda t: t.model.outputList)
    }


class TxListConcatenateModel(AbstractConcatenateModel):
    ROLE_MAP: Final = TxListModel.ROLE_MAP

    def __init__(self, application: Application) -> None:
        super().__init__(application)
        self._unique_map = {}
        self.rowsInserted.connect(self._onRowsInserted)
        self.rowsRemoved.connect(self._onRowsRemoved)

    def isVisibleRow(self, row_index: int, parent: QModelIndex) -> bool:
        index = self.index(row_index, 0, parent)
        value = self.data(index, TxListModel.Role.INSTANCE)
        return self._unique_map.get(value) == row_index

    def _onRowsInserted(
            self,
            parent: QModelIndex,
            first_index: int,
            last_index: int) -> None:
        for i in range(first_index, last_index + 1):
            index = self.index(i, 0, parent)
            value = self.data(index, TxListModel.Role.INSTANCE)
            self._unique_map.setdefault(value, i)

    def _onRowsRemoved(
            self,
            parent: QModelIndex,
            first_index: int,
            last_index: int) -> None:
        for i in range(first_index, last_index + 1):
            index = self.index(i, 0, parent)
            value = self.data(index, TxListModel.Role.INSTANCE)
            if self._unique_map.get(value) == i:
                self._unique_map = {}
                row_count = self.rowCount()
                if row_count > 0:
                    self._onRowsInserted(parent, 0, row_count - 1)
                break


class TxListSortedModel(AbstractListSortedModel):
    def __init__(
            self,
            application: Application,
            source_model: TxListModel) -> None:
        super().__init__(
            application,
            source_model,
            TxListModel.Role.NAME,
            Qt.DescendingOrder)

    def filterAcceptsRow(
            self,
            source_row: int,
            source_parent: QModelIndex) -> bool:
        source_model = self.sourceModel()
        if isinstance(source_model, TxListConcatenateModel):
            return source_model.isVisibleRow(source_row, source_parent)
        return True

    def lessThan(
            self,
            source_left: QModelIndex,
            source_right: QModelIndex) -> bool:
        source_model = self.sourceModel()

        a = source_model.data(source_left, TxListModel.Role.STATE)
        b = source_model.data(source_right, TxListModel.Role.STATE)

        if a.height == -1 and b.height != -1:
            return False
        if a.height != -1 and b.height == -1:
            return True
        if a.height < b.height:
            return True
        if a.height > b.height:
            return False

        # TODO sort by server order

        if a.time < b.time:
            return True
        if a.time > b.time:
            return False

        a = source_model.data(source_left, TxListModel.Role.NAME)
        b = source_model.data(source_right, TxListModel.Role.NAME)
        return a < b
