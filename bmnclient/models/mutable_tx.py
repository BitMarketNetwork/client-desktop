# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot

from . import AbstractModel, AbstractStateModel, ValidStatus
from .amount import AbstractAmountInputModel, AbstractAmountModel
from .tx import TxIoListModel
from ..coin_interfaces import MutableTxInterface

if TYPE_CHECKING:
    from typing import Optional, Sequence
    from ..coins.abstract.coin import AbstractCoin
    from ..ui.gui import Application


class AbstractMutableTxStateModel(AbstractStateModel):
    def __init__(
            self,
            application: Application,
            tx: AbstractCoin.MutableTx) -> None:
        super().__init__(application, tx.coin)
        self._tx = tx


class AbstractMutableTxAmountModel(AbstractAmountModel):
    def __init__(
            self,
            application: Application,
            tx: AbstractCoin.MutableTx) -> None:
        super().__init__(application, tx.coin)
        self._tx = tx

    def _getValue(self) -> Optional[int]:
        raise NotImplementedError


class AbstractMutableTxAmountInputModel(AbstractAmountInputModel):
    def __init__(
            self,
            application: Application,
            tx: AbstractCoin.MutableTx) -> None:
        super().__init__(application, tx.coin)
        self._tx = tx

    def _getValue(self) -> Optional[int]:
        raise NotImplementedError

    def _setValue(self, value: Optional[int]) -> bool:
        raise NotImplementedError

    def _getDefaultValue(self) -> Optional[int]:
        raise NotImplementedError


class MutableTxSourceAmountModel(AbstractMutableTxAmountModel):
    def _getValue(self) -> Optional[int]:
        return self._tx.sourceAmount


class MutableTxAmountModel(AbstractMutableTxAmountInputModel):
    def _getValue(self) -> Optional[int]:
        amount = self._tx.amount
        return None if amount < 0 else amount

    def _setValue(self, value: Optional[int]) -> bool:
        if value is None or value < 0:
            self._tx.amount = -1
            return False
        self._tx.amount = value
        return True

    def _getDefaultValue(self) -> Optional[int]:
        return self._tx.maxAmount

    def _getValidStatus(self) -> ValidStatus:
        if self._tx.isValidAmount:
            return ValidStatus.Accept
        return ValidStatus.Reject


class MutableTxFeeAmountModel(AbstractMutableTxAmountModel):
    __stateChanged = QSignal()

    def _getValue(self) -> Optional[int]:
        amount = self._tx.feeAmount
        return None if amount < 0 else amount

    @QProperty(bool, notify=__stateChanged)
    def subtractFromAmount(self) -> bool:
        return self._tx.subtractFee

    @subtractFromAmount.setter
    def _setSubtractFromAmount(self, value: bool) -> None:
        self._tx.subtractFee = value
        self.refresh()  # TODO kill


class MutableTxKibFeeAmountModel(AbstractMutableTxAmountInputModel):
    def _getValue(self) -> Optional[int]:
        amount = self._tx.feeAmountPerByte
        return None if amount < 0 else (amount * 1024)

    def _setValue(self, value: Optional[int]) -> bool:
        if value is None or value < 0:
            self._tx.feeAmountPerByte = -1
            return False
        self._tx.feeAmountPerByte = value // 1024
        return True

    def _getDefaultValue(self) -> Optional[int]:
        return self._tx.feeAmountPerByteDefault * 1024

    def _getValidStatus(self) -> ValidStatus:
        if self._tx.isValidFeeAmount:
            return ValidStatus.Accept
        return ValidStatus.Reject


class MutableTxChangeAmountModel(AbstractMutableTxAmountModel):
    __stateChanged = QSignal()

    def _getValue(self) -> Optional[int]:
        return self._tx.changeAmount

    @QProperty(bool, notify=__stateChanged)
    def toNewAddress(self) -> bool:
        raise NotImplementedError

    @toNewAddress.setter
    def _setToNewAddress(self, value: bool) -> None:
        raise NotImplementedError

    @QProperty(str, notify=__stateChanged)
    def addressName(self) -> str:
        address = self._tx.changeAddress
        return "-" if address is None else address.name


class MutableTxReceiverModel(AbstractMutableTxStateModel):
    __stateChanged = QSignal()

    def __init__(
            self,
            application: Application,
            tx: AbstractCoin.MutableTx) -> None:
        super().__init__(application, tx)
        self._first_use = True

    @QProperty(str, notify=__stateChanged)
    def addressName(self) -> str:
        if self._tx.receiverAddress is not None:
            return self._tx.receiverAddress.name
        else:
            return ""

    @addressName.setter
    def _setAddressName(self, value: str) -> None:
        self._tx.setReceiverAddressName(value)
        self._first_use = False
        self.refresh()

    def _getValidStatus(self) -> ValidStatus:
        if self._tx.receiverAddress is not None:
            return ValidStatus.Accept
        elif self._first_use:
            return ValidStatus.Unset
        return ValidStatus.Reject


# TODO
class MutableTxSourceListModel(TxIoListModel):
    __stateChanged = QSignal()

    def __init__(self, application: Application, source_list: Sequence) -> None:
        super().__init__(application, source_list)
        # noinspection PyUnresolvedReferences
        self.rowsInserted.connect(lambda **_: self.__stateChanged.emit())
        # noinspection PyUnresolvedReferences
        self.rowsRemoved.connect(lambda **_: self.__stateChanged.emit())

    @QProperty(bool, notify=__stateChanged)
    def useAllInputs(self) -> bool:
        for i in range(0, self.rowCount()):
            state = self.data(self.index(i), self.Role.STATE)
            if not state.useAsTransactionInput:
                return False
        return True

    @useAllInputs.setter
    def _setUseAllInputs(self, value: bool) -> None:
        changed = False
        for i in range(0, self.rowCount()):
            state = self.data(self.index(i), self.Role.STATE)
            if state.useAsTransactionInput != value:
                state.useAsTransactionInput = value
                changed = True
        if changed:
            # noinspection PyUnresolvedReferences
            self.__stateChanged.emit()


class MutableTxModel(MutableTxInterface, AbstractModel):
    __stateChanged = QSignal()

    def __init__(
            self,
            application: Application,
            tx: AbstractCoin.MutableTx) -> None:
        super().__init__(
            application,
            query_scheduler=application.networkQueryScheduler,
            tx=tx)

        self._source_amount = MutableTxSourceAmountModel(
            self._application,
            self._tx)
        self.connectModelRefresh(self._source_amount)

        self._amount = MutableTxAmountModel(
            self._application,
            self._tx)
        self.connectModelRefresh(self._amount)

        self._fee_amount = MutableTxFeeAmountModel(
            self._application,
            self._tx)
        self.connectModelRefresh(self._fee_amount)

        self._kib_fee_amount = MutableTxKibFeeAmountModel(
            self._application,
            self._tx)
        self.connectModelRefresh(self._kib_fee_amount)

        self._change_amount = MutableTxChangeAmountModel(
            self._application,
            self._tx)
        self.connectModelRefresh(self._change_amount)

        self._receiver = MutableTxReceiverModel(
            self._application,
            self._tx)
        self.connectModelRefresh(self._receiver)

        self._source_list = MutableTxSourceListModel(  # TODO
            self._application,
            [])

    @QProperty(str, notify=__stateChanged)
    def name(self) -> str:
        name = self._tx.name
        return "" if name is None else name

    @QProperty(QObject, constant=True)
    def sourceAmount(self) -> MutableTxSourceAmountModel:
        return self._source_amount

    @QProperty(QObject, constant=True)
    def amount(self) -> MutableTxAmountModel:
        return self._amount

    @QProperty(QObject, constant=True)
    def feeAmount(self) -> MutableTxFeeAmountModel:
        return self._fee_amount

    @QProperty(QObject, constant=True)
    def kibFeeAmount(self) -> MutableTxKibFeeAmountModel:
        return self._kib_fee_amount

    @QProperty(QObject, constant=True)
    def changeAmount(self) -> MutableTxChangeAmountModel:
        return self._change_amount

    @QProperty(QObject, constant=True)
    def receiver(self) -> MutableTxReceiverModel:
        return self._receiver

    @QProperty(QObject, constant=True)
    def sourceList(self) -> MutableTxSourceListModel:
        return self._source_list

    # noinspection PyTypeChecker
    @QSlot(result=bool)
    def prepare(self) -> bool:
        return self._tx.prepare()

    # noinspection PyTypeChecker
    @QSlot(result=bool)
    def sign(self) -> bool:
        # TODO ask password
        return self._tx.sign()

    # noinspection PyTypeChecker
    @QSlot(result=bool)
    def broadcast(self) -> bool:
        return self._tx.broadcast()
