# JOK++
from __future__ import annotations

from enum import auto
from typing import Final, Optional, TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QDateTime, \
    Signal as QSignal

from . import AbstractModel, AbstractStateModel
from .address import AddressListModel
from .amount import AmountModel
from .list import \
    AbstractConcatenateModel, \
    AbstractListModel, \
    AbstractListSortedModel, \
    RoleEnum

if TYPE_CHECKING:
    from ..ui.gui import Application
    from ..wallet.tx import Transaction


class AbstractTransactionStateModel(AbstractStateModel):
    def __init__(self, application: Application, tx: Transaction) -> None:
        super().__init__(application, tx.wallet.coin)
        self._tx = tx


class TransactionStateModel(AbstractTransactionStateModel):
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
        return self.locale.integerToString(self._tx.height)

    @QProperty(int, notify=__stateChanged)
    def confirmations(self) -> int:
        return self._tx.confirmCount

    @QProperty(str, notify=__stateChanged)
    def confirmationsHuman(self) -> str:
        return self.locale.integerToString(self._tx.confirmCount)


class TransactionAmountModel(AmountModel):
    def __init__(self, application: Application, tx: Transaction) -> None:
        super().__init__(application, tx.wallet.coin)
        self._tx = tx

    def _getValue(self) -> Optional[int]:
        return self._tx.balance


class TransactionFeeAmountModel(AmountModel):
    def __init__(self, application: Application, tx: Transaction) -> None:
        super().__init__(application, tx.wallet.coin)
        self._tx = tx

    def _getValue(self) -> Optional[int]:
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


class TransactionModel(AbstractModel):
    # TODO
    pass
