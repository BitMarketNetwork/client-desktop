from __future__ import annotations

from abc import ABCMeta
from typing import Optional, Sequence, TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot

from . import AbstractModel, AbstractStateModel, ValidStatus
from .amount import AmountInputModel, AmountModel
from .tx import TxIoListModel
from ..coins.mutable_tx import MutableTxModelInterface

if TYPE_CHECKING:
    from ..ui.gui import Application
    from ..wallet.mutable_tx import MutableTransaction


class AbstractTxBroadcastStateModel(AbstractStateModel):
    def __init__(
            self,
            application: Application,
            tx: MutableTransaction) -> None:
        super().__init__(application, tx.coin)
        self._tx = tx


class AbstractTxAmountModel(AmountModel, metaclass=ABCMeta):
    def __init__(
            self,
            application: Application,
            tx: MutableTransaction) -> None:
        super().__init__(application, tx.coin)
        self._tx = tx


class AbstractTxAmountInputModel(AmountInputModel, metaclass=ABCMeta):
    def __init__(
            self,
            application: Application,
            tx: MutableTransaction) -> None:
        super().__init__(application, tx.coin)
        self._tx = tx


class MutableTxSourceAmountModel(AbstractTxAmountModel):
    def _getValue(self) -> Optional[int]:
        return self._tx.sourceAmount


class TxBroadcastAmountModel(AbstractTxAmountInputModel):
    def _getValue(self) -> Optional[int]:
        return None if self._tx.amount < 0 else self._tx.amount  # TODO

    def _setValue(self, value: Optional[int]) -> bool:
        if value is None or value < 0:
            self._tx.amount = -1   # TODO
            return False
        self._tx.amount = value
        return True

    def _getDefaultValue(self) -> Optional[int]:
        v = self._tx.get_max_amount()
        return None if v < 0 else v   # TODO

    def _getValidStatus(self) -> ValidStatus:
        if self._tx.amount >= 0 and self._tx.change >= 0:   # TODO
            if self._tx.amount <= self._tx.sourceAmount:
                return ValidStatus.Accept
        return ValidStatus.Reject


class TxBroadcastFeeAmountModel(AbstractTxAmountModel):
    __stateChanged = QSignal()

    def _getValue(self) -> Optional[int]:
        return None if self._tx.spb < 0 else self._tx.fee  # TODO

    @QProperty(bool, notify=__stateChanged)
    def subtractFromAmount(self) -> bool:
        return self._tx.subtract_fee

    @subtractFromAmount.setter
    def _setSubtractFromAmount(self, value: bool) -> None:
        if value != self._tx.subtract_fee:
            self._tx.subtract_fee = value
            self.refresh()


class TxBroadcastKibFeeAmountModel(
        AbstractTxAmountInputModel):
    def _getValue(self) -> Optional[int]:
        return None if self._tx.spb < 0 else (self._tx.spb * 1024)  # TODO

    def _setValue(self, value: Optional[int]) -> bool:
        if value is None or value < 0:
            self._tx.spb = -1
            return False
        self._tx.spb = value // 1024
        return True

    def _getDefaultValue(self) -> Optional[int]:
        v = self._tx.spb_default()
        return None if v < 0 else (v * 1024)

    def _getValidStatus(self) -> ValidStatus:
        if self._tx.spb < 0:  # TODO
            return ValidStatus.Reject
        if self._tx.subtract_fee and self._tx.fee > self._tx.amount:  # TODO
            return ValidStatus.Reject
        return ValidStatus.Accept


class TxBroadcastChangeAmountModel(AbstractTxAmountModel):
    __stateChanged = QSignal()

    def _getValue(self) -> Optional[int]:
        return self._tx.change

    @QProperty(bool, notify=__stateChanged)
    def toNewAddress(self) -> bool:
        return self._tx.new_address_for_change

    @toNewAddress.setter
    def _setToNewAddress(self, value: bool) -> None:
        if value != self._tx.new_address_for_change:
            self._tx.new_address_for_change = value
            self.refresh()

    @QProperty(str, notify=__stateChanged)
    def addressName(self) -> str:
        return self._tx.leftover_address


class MutableTxReceiverModel(AbstractTxBroadcastStateModel):
    __stateChanged = QSignal()

    def __init__(
            self,
            application: Application,
            tx: MutableTransaction) -> None:
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


class TxBroadcastInputListModel(TxIoListModel):
    __stateChanged = QSignal()

    def __init__(self, application: Application, source_list: Sequence) -> None:
        super().__init__(application, source_list)
        self.rowsInserted.connect(lambda **_: self.__stateChanged.emit())
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
            self.__stateChanged.emit()


class MutableTxModel(MutableTxModelInterface, AbstractModel):
    __stateChanged = QSignal()

    def __init__(
            self,
            application: Application,
            tx: MutableTransaction) -> None:
        super().__init__(application)
        self._tx = tx

        self._source_amount = MutableTxSourceAmountModel(
            self._application,
            self._tx)
        self.connectModelRefresh(self._source_amount)

        self._amount = TxBroadcastAmountModel(
            self._application,
            self._tx)
        self.connectModelRefresh(self._amount)

        self._fee_amount = TxBroadcastFeeAmountModel(
            self._application,
            self._tx)
        self.connectModelRefresh(self._fee_amount)

        self._kib_fee_amount = TxBroadcastKibFeeAmountModel(
            self._application,
            self._tx)
        self.connectModelRefresh(self._kib_fee_amount)

        self._change_amount = TxBroadcastChangeAmountModel(
            self._application,
            self._tx)
        self.connectModelRefresh(self._change_amount)

        self._receiver = MutableTxReceiverModel(
            self._application,
            self._tx)
        self.connectModelRefresh(self._receiver)

        self._input_list = TxBroadcastInputListModel(
            self._application,
            self._tx.sources)

    @QProperty(str, notify=__stateChanged)
    def name(self) -> str:
        return self._tx.tx_id

    @QProperty(QObject, constant=True)
    def sourceAmount(self) -> MutableTxSourceAmountModel:
        return self._source_amount

    @QProperty(QObject, constant=True)
    def amount(self) -> TxBroadcastAmountModel:
        return self._amount

    @QProperty(QObject, constant=True)
    def feeAmount(self) -> TxBroadcastFeeAmountModel:
        return self._fee_amount

    @QProperty(QObject, constant=True)
    def kibFeeAmount(self) -> TxBroadcastKibFeeAmountModel:
        return self._kib_fee_amount

    @QProperty(QObject, constant=True)
    def changeAmount(self) -> TxBroadcastChangeAmountModel:
        return self._change_amount

    @QProperty(QObject, constant=True)
    def receiver(self) -> MutableTxReceiverModel:
        return self._receiver

    @QProperty(QObject, constant=True)
    def inputList(self) -> TxBroadcastInputListModel:
        return self._input_list

    # noinspection PyTypeChecker
    @QSlot(result=bool)
    def prepare(self) -> bool:
        self._tx.prepare()
        return True

    # noinspection PyTypeChecker
    @QSlot(result=bool)
    def sign(self) -> bool:  # TODO ask password
        pass

    # noinspection PyTypeChecker
    @QSlot(result=bool)
    def broadcast(self) -> bool:
        self._tx.send()  # TODO result
        return True
