# JOK++
from __future__ import annotations

from enum import auto

from PySide2.QtCore import \
    Property as QProperty, \
    QDateTime, \
    QLocale, \
    Signal as QSignal

from . import \
    AbstractAmountModel, \
    AbstractListModel, \
    AbstractListSortedModel, \
    AbstractTxStateModel, \
    RoleEnum


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

    @QProperty(str, notify=_stateChanged)
    def heightHuman(self) -> str:
        return self._application.language.locale.integerToString(
            self._tx.height)

    @QProperty(int, notify=_stateChanged)
    def confirmations(self) -> int:
        return self._tx.confirmCount

    @QProperty(str, notify=_stateChanged)
    def confirmationsHuman(self) -> str:
        return self._application.language.locale.integerToString(
            self._tx.confirmCount)


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


class TxListSortedModel(AbstractListSortedModel):
    def __init__(self, source_model: TxListModel) -> None:
        super().__init__(source_model, TxListModel.Role.NAME)
