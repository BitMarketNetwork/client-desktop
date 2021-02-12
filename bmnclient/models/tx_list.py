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
    AbstractConcatenateModel, \
    AbstractListModel, \
    AbstractListSortedModel, \
    AbstractTransactionStateModel, \
    RoleEnum
from .address_list import AddressListModel
from .amount import AmountModel

if TYPE_CHECKING:
    from ..ui.gui import Application
    from ..wallet.tx import Transaction


class TransactionStateModel(AbstractTransactionStateModel):
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


class TransactionAmountModel(AmountModel):
    def __init__(self, application: Application, tx: Transaction) -> None:
        super().__init__(application, tx.wallet.coin)
        self._tx = tx

    def _getValue(self) -> int:
        return self._tx.balance


class TransactionFeeAmountModel(AmountModel):
    def __init__(self, application: Application, tx: Transaction) -> None:
        super().__init__(application, tx.wallet.coin)
        self._tx = tx

    def _getValue(self) -> int:
        return self._tx.fee


class TransactionIoListModel(AddressListModel):
    pass


class TransactionListModel(AbstractListModel):
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


class TransactionListConcatenateModel(AbstractConcatenateModel):
    ROLE_MAP: Final = TransactionListModel.ROLE_MAP


class TransactionListSortedModel(AbstractListSortedModel):
    def __init__(
            self,
            application: Application,
            source_model: TransactionListModel) -> None:
        super().__init__(
            application,
            source_model,
            TransactionListModel.Role.HASH)
