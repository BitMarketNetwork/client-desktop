from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot

from . import AbstractModel, AbstractStateModel, ValidStatus
from .address import AddressListModel
from .amount import AmountInputModel, AmountModel

if TYPE_CHECKING:
    from ..ui.gui import Application
    from ..wallet.mutable_tx import MutableTransaction


class AbstractTransactionBroadcastStateModel(AbstractStateModel):
    def __init__(
            self,
            application: Application,
            tx: MutableTransaction) -> None:
        super().__init__(application, tx.coin)
        self._tx = tx


class TransactionBroadcastAvailableAmountModel(AmountModel):
    def __init__(
            self,
            application: Application,
            tx: MutableTransaction) -> None:
        super().__init__(application, tx.coin)
        self._tx = tx

    def _getValue(self) -> Optional[int]:
        return self._tx.source_amount


class TransactionBroadcastAmountModel(AmountInputModel):
    def __init__(
            self,
            application: Application,
            tx: MutableTransaction) -> None:
        super().__init__(application, tx.coin)
        self._tx = tx

    def _getValue(self) -> Optional[int]:
        return None if self._tx.amount < 0 else self._tx.amount  # TODO

    def _getDefaultValue(self) -> Optional[int]:
        v = self._tx.get_max()
        return None if v < 0 else v

    def _setValue(self, value: Optional[int]) -> bool:
        if value is None or value < 0:
            self._tx.amount = -1   # TODO
            return False
        else:
            self._tx.amount = value
            return True

    def _getValidStatus(self) -> ValidStatus:
        if self._tx.amount >= 0:   # TODO
            return ValidStatus.Accept
        else:
            return ValidStatus.Reject


class TransactionBroadcastFeeAmountModel(AmountInputModel):
    __stateChanged = QSignal()

    def __init__(
            self,
            application: Application,
            tx: MutableTransaction) -> None:
        super().__init__(application, tx.coin)
        self._tx = tx

    def _getValue(self) -> Optional[int]:
        return self._tx.fee

    def _setValue(self, value: int) -> bool:
        if value < 0:
            # TODO set _tx invalid value
            return False
        self._tx.fee = value
        return True

    def _setDefaultValue(self) -> bool:
        self._tx.spb = -1  # TODO
        return True

    @QProperty(str, notify=__stateChanged)
    def amountPerKiBHuman(self) -> str:
        return self._toHumanValue(self._tx.spb * 1024, self._coin.currency)

    # noinspection PyTypeChecker
    @QSlot(str, result=bool)
    def setAmountPerKiBHuman(self, value: str) -> bool:
        value = self._fromHumanValue(value, self._coin.currency)
        if value is None or value < 0:
            # TODO set _tx invalid value
            return False
        value //= 1024
        if self._tx.spb != value:
            self._tx.spb = value
            self.refresh()
        return True

    @QProperty(bool, notify=__stateChanged)
    def subtractFromAmount(self) -> bool:
        return self._tx.subtract_fee

    # noinspection PyTypeChecker
    @QSlot(bool, result=bool)
    def setSubtractFromAmount(self, value: bool) -> bool:
        if value != self._tx.subtract_fee:
            self._tx.subtract_fee = value
            self.refresh()
        return True


class TransactionBroadcastChangeAmountModel(AmountModel):
    __stateChanged = QSignal()

    def __init__(
            self,
            application: Application,
            tx: MutableTransaction) -> None:
        super().__init__(application, tx.coin)
        self._tx = tx

    def _getValue(self) -> Optional[int]:
        return self._tx.change

    @QProperty(bool, notify=__stateChanged)
    def toNewAddress(self) -> bool:
        return self._tx.new_address_for_change

    # noinspection PyTypeChecker
    @QSlot(bool, result=bool)
    def setToNewAddress(self, value: bool) -> bool:
        if value != self._tx.new_address_for_change:
            self._tx.new_address_for_change = value
            self.refresh()
        return True


class TransactionBroadcastReceiverModel(AbstractTransactionBroadcastStateModel):
    __stateChanged = QSignal()

    def __init__(
            self,
            application: Application,
            tx: MutableTransaction) -> None:
        super().__init__(application, tx)
        self._first_use = True

    @QProperty(str, notify=__stateChanged)
    def addressName(self) -> str:
        return self._tx.receiver

    # noinspection PyTypeChecker
    @QSlot(str, result=bool)
    def setAddressName(self, name: str) -> bool:
        r = self._tx.setReceiverAddressName(name)
        self._first_use = False
        self.refresh()
        return r

    def _getValidStatus(self) -> ValidStatus:
        if self._tx.receiver_valid:
            return ValidStatus.Accept
        elif self._first_use:
            return ValidStatus.Unset
        return ValidStatus.Reject


class TransactionBroadcastModel(AbstractModel):
    def __init__(
            self,
            application: Application,
            tx: MutableTransaction) -> None:
        super().__init__(application)
        self._tx = tx

        self._available_amount = TransactionBroadcastAvailableAmountModel(
            self._application,
            self._tx)
        self.connectModelRefresh(self._available_amount)

        self._amount = TransactionBroadcastAmountModel(
            self._application,
            self._tx)
        self.connectModelRefresh(self._amount)

        self._fee_amount = TransactionBroadcastFeeAmountModel(
            self._application,
            self._tx)
        self.connectModelRefresh(self._fee_amount)

        self._change_amount = TransactionBroadcastChangeAmountModel(
            self._application,
            self._tx)
        self.connectModelRefresh(self._change_amount)

        self._receiver = TransactionBroadcastReceiverModel(
            self._application,
            self._tx)
        self.connectModelRefresh(self._receiver)

        self._address_input_list = AddressListModel(
            self._application,
            self._tx.sources)

    @QProperty(QObject, constant=True)
    def availableAmount(self) -> TransactionBroadcastAvailableAmountModel:
        return self._available_amount

    @QProperty(QObject, constant=True)
    def amount(self) -> TransactionBroadcastAmountModel:
        return self._amount

    @QProperty(QObject, constant=True)
    def feeAmount(self) -> TransactionBroadcastFeeAmountModel:
        return self._fee_amount

    @QProperty(QObject, constant=True)
    def changeAmount(self) -> TransactionBroadcastChangeAmountModel:
        return self._change_amount

    @QProperty(QObject, constant=True)
    def receiver(self) -> TransactionBroadcastReceiverModel:
        return self._receiver

    @QProperty(QObject, constant=True)
    def addressInputList(self) -> AddressListModel:
        return self._address_input_list
