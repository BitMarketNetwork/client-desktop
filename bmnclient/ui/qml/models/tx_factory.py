from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot

from . import AbstractCoinStateModel, AbstractModel, ValidStatus
from .amount import AbstractAmountInputModel, AbstractAmountModel
from .tx import TxIoListModel
from ....coin_interfaces import TxFactoryInterface
from ..dialogs.tx import TxBroadcastPendingDialog
if TYPE_CHECKING:
    from typing import Optional, Sequence
    from .. import QmlApplication
    from ....coins.abstract.coin import AbstractCoin


class AbstractTxFactoryStateModel(AbstractCoinStateModel):
    def __init__(
            self,
            application: QmlApplication,
            factory: AbstractCoin.TxFactory) -> None:
        super().__init__(application, factory.coin)
        self._factory = factory


class TxFactoryStateModel(AbstractTxFactoryStateModel):
    __stateChanged = QSignal()

    @QProperty(str, notify=__stateChanged)
    def estimatedRawSizeHuman(self) -> str:
        s = self._factory.estimatedRawSize
        if s < 0:
            return self._NONE_STRING
        return "~" + self.locale.integerToString(s)

    @QProperty(str, notify=__stateChanged)
    def estimatedVirtualSizeHuman(self) -> str:
        s = self._factory.estimatedVirtualSize
        if s < 0:
            return self._NONE_STRING
        return "~" + self.locale.integerToString(s)


class AbstractTxFactoryAmountModel(AbstractAmountModel):
    def __init__(
            self,
            application: QmlApplication,
            factory: AbstractCoin.TxFactory) -> None:
        super().__init__(application, factory.coin)
        self._factory = factory

    def _getValue(self) -> Optional[int]:
        raise NotImplementedError


class AbstractTxFactoryAmountInputModel(AbstractAmountInputModel):
    def __init__(
            self,
            application: QmlApplication,
            factory: AbstractCoin.TxFactory) -> None:
        super().__init__(application, factory.coin)
        self._factory = factory

    def _getValue(self) -> Optional[int]:
        raise NotImplementedError

    def _setValue(self, value: Optional[int]) -> bool:
        raise NotImplementedError

    def _setDefaultValue(self) -> bool:
        raise NotImplementedError


class TxFactoryAvailableAmountModel(AbstractTxFactoryAmountModel):
    def _getValue(self) -> Optional[int]:
        return self._factory.availableAmount


class TxFactoryReceiverAmountModel(AbstractTxFactoryAmountInputModel):
    def _getValue(self) -> Optional[int]:
        amount = self._factory.receiverAmount
        return None if amount < 0 else amount

    def _setValue(self, value: Optional[int]) -> bool:
        if value is None or value < 0:
            self._factory.receiverAmount = -1
            return False
        self._factory.receiverAmount = value
        return True

    def _setDefaultValue(self) -> bool:
        self._factory.setReceiverMaxAmount()
        return True

    def _getValidStatus(self) -> ValidStatus:
        if self._factory.isValidReceiverAmount:
            return super()._getValidStatus()
        return ValidStatus.Reject


class TxFactoryFeeAmountModel(AbstractTxFactoryAmountModel):
    __stateChanged = QSignal()

    def _getValue(self) -> Optional[int]:
        return self._factory.feeAmount

    @QProperty(bool, notify=__stateChanged)
    def subtractFromAmount(self) -> bool:
        return self._factory.subtractFee

    @subtractFromAmount.setter
    def subtractFromAmount(self, value: bool) -> None:
        self._factory.subtractFee = value
        self.update()  # TODO kill


class TxFactoryKibFeeAmountModel(AbstractTxFactoryAmountInputModel):
    def _getValue(self) -> Optional[int]:
        amount = self._factory.feeAmountPerByte
        return None if amount < 0 else (amount * 1024)

    def _setValue(self, value: Optional[int]) -> bool:
        if value is None or value < 0:
            self._factory.feeAmountPerByte = -1
            return False
        self._factory.feeAmountPerByte = value // 1024
        return True

    def _setDefaultValue(self) -> bool:
        self._factory.feeAmountPerByte = self._factory.feeAmountPerByteDefault
        return True

    def _getValidStatus(self) -> ValidStatus:
        if self._factory.isValidFeeAmount:
            return super()._getValidStatus()
        return ValidStatus.Reject


class TxFactoryChangeAmountModel(AbstractTxFactoryAmountModel):
    __stateChanged = QSignal()

    def _getValue(self) -> Optional[int]:
        return self._factory.changeAmount

    @QProperty(bool, notify=__stateChanged)
    def toNewAddress(self) -> bool:
        raise NotImplementedError

    @toNewAddress.setter
    def toNewAddress(self, value: bool) -> None:
        raise NotImplementedError

    @QProperty(str, notify=__stateChanged)
    def addressName(self) -> str:
        address = self._factory.changeAddress
        return address.name if address is not None else self._NONE_STRING


class TxFactoryReceiverModel(AbstractTxFactoryStateModel):
    __stateChanged = QSignal()

    def __init__(
            self,
            application: QmlApplication,
            factory: AbstractCoin.TxFactory) -> None:
        super().__init__(application, factory)
        self._first_use = True

    @QProperty(str, notify=__stateChanged)
    def addressName(self) -> str:
        if self._factory.receiverAddress is not None:
            return self._factory.receiverAddress.name
        else:
            return ""

    @addressName.setter
    def addressName(self, value: str) -> None:
        self._factory.setReceiverAddressName(value)
        self._first_use = False

    @QProperty(str, notify=__stateChanged)
    def inputAddressName(self) -> str:
        if self._factory.inputAddress is not None:
            return self._factory.inputAddress.name
        else:
            return ""

    @inputAddressName.setter
    def inputAddressName(self, value: str) -> None:
        self._factory.setInputAddressName(value)

    def _getValidStatus(self) -> ValidStatus:
        if self._factory.receiverAddress is not None:
            return super()._getValidStatus()
        elif self._first_use:
            return ValidStatus.Unset
        return ValidStatus.Reject


# TODO
class TxFactorySourceListModel(TxIoListModel):
    __stateChanged = QSignal()

    def __init__(
            self,
            application: QmlApplication,
            source_list: Sequence) -> None:
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
    def useAllInputs(self, value: bool) -> None:
        changed = False
        for i in range(0, self.rowCount()):
            state = self.data(self.index(i), self.Role.STATE)
            if state.useAsTransactionInput != value:
                state.useAsTransactionInput = value
                changed = True
        if changed:
            # noinspection PyUnresolvedReferences
            self.__stateChanged.emit()


class TxFactoryModel(TxFactoryInterface, AbstractModel):
    __stateChanged = QSignal()

    def __init__(
            self,
            application: QmlApplication,
            factory: AbstractCoin.TxFactory) -> None:
        super().__init__(
            application,
            query_scheduler=application.networkQueryScheduler,
            database=application.database,
            factory=factory)

        self._state = TxFactoryStateModel(
            self._application,
            self._factory)
        self.connectModelUpdate(self._state)

        self._available_amount = TxFactoryAvailableAmountModel(
            self._application,
            self._factory)
        self.connectModelUpdate(self._available_amount)

        self._receiver_amount = TxFactoryReceiverAmountModel(
            self._application,
            self._factory)
        self.connectModelUpdate(self._receiver_amount)

        self._fee_amount = TxFactoryFeeAmountModel(
            self._application,
            self._factory)
        self.connectModelUpdate(self._fee_amount)

        self._kib_fee_amount = TxFactoryKibFeeAmountModel(
            self._application,
            self._factory)
        self.connectModelUpdate(self._kib_fee_amount)

        self._change_amount = TxFactoryChangeAmountModel(
            self._application,
            self._factory)
        self.connectModelUpdate(self._change_amount)

        self._receiver = TxFactoryReceiverModel(
            self._application,
            self._factory)
        self.connectModelUpdate(self._receiver)

        self._source_list = TxFactorySourceListModel(  # TODO
            self._application,
            [])

    @QProperty(str, notify=__stateChanged)
    def name(self) -> str:
        name = self._factory.name
        return "" if name is None else name

    @QProperty(QObject, constant=True)
    def state(self) -> TxFactoryStateModel:
        return self._state

    @QProperty(QObject, constant=True)
    def availableAmount(self) -> TxFactoryAvailableAmountModel:
        return self._available_amount

    @QProperty(QObject, constant=True)
    def receiverAmount(self) -> TxFactoryReceiverAmountModel:
        return self._receiver_amount

    @QProperty(QObject, constant=True)
    def feeAmount(self) -> TxFactoryFeeAmountModel:
        return self._fee_amount

    @QProperty(QObject, constant=True)
    def kibFeeAmount(self) -> TxFactoryKibFeeAmountModel:
        return self._kib_fee_amount

    @QProperty(QObject, constant=True)
    def changeAmount(self) -> TxFactoryChangeAmountModel:
        return self._change_amount

    @QProperty(QObject, constant=True)
    def receiver(self) -> TxFactoryReceiverModel:
        return self._receiver

    @QProperty(QObject, constant=True)
    def sourceList(self) -> TxFactorySourceListModel:
        return self._source_list

    # noinspection PyTypeChecker
    @QSlot(result=bool)
    def prepare(self) -> bool:
        return self._factory.prepare()

    # noinspection PyTypeChecker
    @QSlot(result=bool)
    def sign(self) -> bool:
        # TODO ask password
        return self._factory.sign()

    # noinspection PyTypeChecker
    @QSlot(result=bool)
    def broadcast(self) -> bool:
        return self._factory.broadcast()

    def afterUpdateState(self) -> None:
        super().afterUpdateState()
        # TODO

    def afterSetInputAddress(self) -> None:
        self._receiver.update()

    def afterSetReceiverAddress(self) -> None:
        self._receiver.update()

    def onBroadcast(self, mtx: AbstractCoin.TxFactory.MutableTx) -> None:
        super().onBroadcast(mtx)
        TxBroadcastPendingDialog(self._application.qmlContext.dialogManager, mtx).open()
        # TODO show pending dialog

    def onBroadcastFinished(
            self,
            error_code: int,
            mtx: AbstractCoin.TxFactory.MutableTx) -> None:
        super().onBroadcastFinished(error_code, mtx)
        # TODO show finished message
