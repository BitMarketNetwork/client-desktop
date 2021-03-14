# JOK++
from __future__ import annotations

from abc import ABCMeta
from enum import auto
from typing import Final, Optional, TYPE_CHECKING

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
    from ..ui.gui import Application
    from ..coins.tx import AbstractTx, AbstractTxIo


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
        return self._tx.status

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
        return self._tx.balance


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

    def beforeAppendInput(self, tx_input: AbstractTxIo) -> None:
        self._input_list_model.lock(self._input_list_model.lockInsertRows())

    def afterAppendInput(self, tx_input: AbstractTxIo) -> None:
        self._input_list_model.unlock()

    def beforeAppendOutput(self, tx_output: AbstractTxIo) -> None:
        self._output_list_model.lock(self._output_list_model.lockInsertRows())

    def afterAppendOutput(self, tx_output: AbstractTxIo) -> None:
        self._output_list_model.unlock()


class TxIoListModel(AddressListModel):
    pass


class TxListModel(AbstractListModel):
    class Role(RoleEnum):
        HASH: Final = auto()
        AMOUNT: Final = auto()
        FEE_AMOUNT: Final = auto()
        STATE: Final = auto()
        INPUT_LIST: Final = auto()
        OUTPUT_LIST: Final = auto()

    ROLE_MAP: Final = {
        Role.HASH: (
            b"hash",
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


class TxListSortedModel(AbstractListSortedModel):
    def __init__(
            self,
            application: Application,
            source_model: TxListModel) -> None:
        super().__init__(
            application,
            source_model,
            TxListModel.Role.HASH)
