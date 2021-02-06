# JOK++
from __future__ import annotations

from enum import auto
from typing import Final, TYPE_CHECKING

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

if TYPE_CHECKING:
    from ..ui.gui import Application
    from ..wallet.coins import CoinType


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


class TxAmountModel(AbstractAmountModel, AbstractTxStateModel):
    def __init__(self, application: Application, coin: CoinType):
        super().__init__(application, coin)

    def _value(self) -> int:
        return self._tx.balance

    def _fiatValue(self) -> float:
        return self._tx.fiatBalance


class TxFeeAmountModel(AbstractAmountModel, AbstractTxStateModel):
    def __init__(self, application: Application, coin: CoinType):
        super().__init__(application, coin)

    def _value(self) -> int:
        return self._tx.fee

    def _fiatValue(self) -> float:
        return self._tx.feeFiatBalance


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
            lambda t: t.inputListModel),
        Role.OUTPUT_LIST: (
            b"outputList",
            lambda t: t.outputListModel)
    }


class TxListConcatenateModel(AbstractConcatenateModel):
    ROLE_MAP: Final = TxListModel.ROLE_MAP


class TxListSortedModel(AbstractListSortedModel):
    def __init__(
            self,
            application: Application,
            source_model: TxListModel) -> None:
        super().__init__(application, source_model, TxListModel.Role.HASH)
