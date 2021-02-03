# JOK++
from __future__ import annotations

from enum import auto
from typing import Final

from PySide2.QtCore import \
    Property as QProperty, \
    QDateTime, \
    QLocale, \
    Signal as QSignal

from . import \
    AbstractAmountModel, \
    AbstractConcatenateModel, \
    AbstractListModel, \
    AbstractListSortedModel, \
    AbstractTxStateModel, \
    RoleEnum


class TxStateModel(AbstractTxStateModel):
    _stateChanged: Final = QSignal()

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


class TxAmountModel(AbstractTxStateModel, AbstractAmountModel):
    def _value(self) -> int:
        return self._tx.balance

    def _fiatValue(self) -> float:
        return self._tx.fiatBalance


class TxFeeAmountModel(AbstractTxStateModel, AbstractAmountModel):
    def _value(self) -> int:
        return self._tx.fee

    def _fiatValue(self) -> float:
        return self._tx.feeFiatBalance


class TxListModel(AbstractListModel):
    class Role(RoleEnum):
        NAME: Final = auto()
        AMOUNT: Final = auto()
        FEE_AMOUNT: Final = auto()
        STATE: Final = auto()
        INPUT_LIST: Final = auto()
        OUTPUT_LIST: Final = auto()

    ROLE_MAP: Final = {
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


class TxListConcatenateModel(AbstractConcatenateModel):
    ROLE_MAP: Final = TxListModel.ROLE_MAP


class TxListSortedModel(AbstractListSortedModel):
    def __init__(self, source_model: TxListModel) -> None:
        super().__init__(source_model, TxListModel.Role.NAME)
