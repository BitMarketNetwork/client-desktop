from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import (
    Property as QProperty,
    QDateTime,
    QObject,
    Signal as QSignal,
    Slot as QSlot)

from . import AbstractCoinStateModel, AbstractModel
from .abstract import AbstractCoinObjectModel, AbstractTableModel
from .amount import AbstractAmountModel
from .tx_io import TxIoListModel
from ....coins.abstract import Coin

if TYPE_CHECKING:
    from .. import QmlApplication


class AbstractTxStateModel(AbstractCoinStateModel):
    def __init__(
            self,
            application: QmlApplication,
            tx: Coin.Tx) -> None:
        super().__init__(application, tx.coin)
        self._tx = tx


class AbstractTxAmountModel(AbstractAmountModel):
    def __init__(
            self,
            application: QmlApplication,
            tx: Coin.Tx) -> None:
        super().__init__(application, tx.coin)
        self._tx = tx

    def _getValue(self) -> int | None:
        raise NotImplementedError


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
        value = QDateTime()
        value.setSecsSinceEpoch(self._tx.time)
        return self.locale.toString(value, self.locale.FormatType.LongFormat)

    @QProperty(int, notify=__stateChanged)
    def height(self) -> int:
        return self._tx.height

    @QProperty(str, notify=__stateChanged)
    def heightHuman(self) -> str:
        if self._tx.height < 0:
            return self._NONE_STRING
        return self.locale.integerToString(self._tx.height)

    @QProperty(int, notify=__stateChanged)
    def confirmations(self) -> int:
        return self._tx.confirmations

    @QProperty(str, notify=__stateChanged)
    def confirmationsHuman(self) -> str:
        return self.locale.integerToString(self._tx.confirmations)


class TxAmountModel(AbstractTxAmountModel):
    def update(self) -> None:
        super().update()
        for io in self._tx.inputList:
            io.model.amount.update()
        for io in self._tx.outputList:
            io.model.amount.update()

    def _getValue(self) -> int | None:
        return self._tx.amount


class TxFeeAmountModel(AbstractTxAmountModel):
    def _getValue(self) -> int | None:
        return self._tx.feeAmount


class TxModel(AbstractCoinObjectModel, Coin.Tx.Model, AbstractModel):
    def __init__(self, application: QmlApplication, tx: Coin.Tx) -> None:
        super().__init__(application, tx=tx)

        self._amount_model = TxAmountModel(
            self._application,
            self._tx)
        self.connectModelUpdate(self._amount_model)

        self._fee_amount_model = TxFeeAmountModel(
            self._application,
            self._tx)
        self.connectModelUpdate(self._fee_amount_model)

        self._state_model = TxStateModel(
            self._application,
            self._tx)
        self.connectModelUpdate(self._state_model)

    @QProperty(str, constant=True)
    def name(self) -> str:
        return self._tx.name

    @QProperty(str, constant=True)
    def nameHuman(self) -> str:
        return self._tx.nameHuman

    @QProperty(QObject, constant=True)
    def amount(self) -> TxAmountModel:
        return self._amount_model

    @QProperty(QObject, constant=True)
    def feeAmount(self) -> TxFeeAmountModel:
        return self._fee_amount_model

    @QProperty(QObject, constant=True)
    def state(self) -> TxStateModel:
        return self._state_model

    # noinspection PyTypeChecker
    @QSlot(int, result=QObject)
    def openInputList(self, column_count: int) -> TxIoListModel:
        return self._registerList(TxIoListModel(
            self._application,
            self._tx.inputList,
            column_count))

    # noinspection PyTypeChecker
    @QSlot(int, result=QObject)
    def openOutputList(self, column_count: int) -> TxIoListModel:
        return self._registerList(TxIoListModel(
            self._application,
            self._tx.outputList,
            column_count))

    def afterSetHeight(self, value: int) -> None:
        self._state_model.update()
        # noinspection PyUnresolvedReferences
        super().afterSetHeight(value)

    def afterSetTime(self, value: int) -> None:
        self._state_model.update()
        # noinspection PyUnresolvedReferences
        super().afterSetTime(value)


class TxListModel(AbstractTableModel):
    pass
