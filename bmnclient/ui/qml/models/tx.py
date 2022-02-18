from __future__ import annotations

from enum import auto
from typing import TYPE_CHECKING

from PySide6.QtCore import (
    Property as QProperty,
    QDateTime,
    QModelIndex,
    QObject,
    Qt,
    Signal as QSignal)

from . import AbstractCoinStateModel, AbstractModel
from .amount import AbstractAmountModel
from .list import (
    AbstractConcatenateModel,
    AbstractListModel,
    AbstractListSortedModel,
    RoleEnum)
from .tx_io import TxIoListModel
from ....coin_interfaces import TxInterface

if TYPE_CHECKING:
    from typing import Final, Optional
    from .. import QmlApplication
    from ....coins.abstract import Coin


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

    def _getValue(self) -> Optional[int]:
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
        return self.locale.toString(value, self.locale.LongFormat)

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
            io.address.model.amount.update()
        for io in self._tx.outputList:
            io.address.model.amount.update()

    def _getValue(self) -> Optional[int]:
        return self._tx.amount


class TxFeeAmountModel(AbstractTxAmountModel):
    def _getValue(self) -> Optional[int]:
        return self._tx.feeAmount


class TxModel(TxInterface, AbstractModel):
    def __init__(
            self,
            application: QmlApplication,
            tx: Coin.Tx) -> None:
        super().__init__(
            application,
            query_scheduler=application.networkQueryScheduler,
            database=application.database,
            tx=tx)

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

        self._input_list_model = TxIoListModel(
            self._application,
            self._tx.inputList)
        self._output_list_model = TxIoListModel(
            self._application,
            self._tx.outputList)

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

    @QProperty(QObject, constant=True)
    def inputList(self) -> TxIoListModel:
        return self._input_list_model

    @QProperty(QObject, constant=True)
    def outputList(self) -> TxIoListModel:
        return self._output_list_model

    def afterSetHeight(self) -> None:
        self._state_model.update()
        super().afterSetHeight()

    def afterSetTime(self) -> None:
        self._state_model.update()
        super().afterSetTime()


class TxListModel(AbstractListModel):
    class Role(RoleEnum):
        ID: Final = auto()
        VISIBLE: Final = auto()  # for TxListConcatenateModel
        NAME: Final = auto()
        NAME_HUMAN: Final = auto()
        AMOUNT: Final = auto()
        FEE_AMOUNT: Final = auto()
        STATE: Final = auto()
        INPUT_LIST: Final = auto()
        OUTPUT_LIST: Final = auto()

    ROLE_MAP: Final = {
        Role.ID: (
            b"_id",
            lambda t: t.name),
        Role.VISIBLE: (
            b"_visible",
            "_visible"),
        Role.NAME: (
            b"name",
            lambda t: t.model.name),
        Role.NAME_HUMAN: (
            b"nameHuman",
            lambda t: t.model.nameHuman),
        Role.AMOUNT: (
            b"amount",
            lambda t: t.model.amount),
        Role.FEE_AMOUNT: (
            b"feeAmount",
            lambda t: t.model.feeAmount),
        Role.STATE: (
            b"state",
            lambda t: t.model.state),
        Role.INPUT_LIST: (
            b"inputList",
            lambda t: t.model.inputList),
        Role.OUTPUT_LIST: (
            b"outputList",
            lambda t: t.model.outputList)
    }


class TxListConcatenateModel(AbstractConcatenateModel):
    ROLE_MAP: Final = TxListModel.ROLE_MAP

    def isVisibleRow(self, row_index: int, parent: QModelIndex) -> bool:
        index = self.index(row_index, 0, parent)
        if self.data(index, TxListModel.Role.VISIBLE):
            return True

        id_ = self.data(index, TxListModel.Role.ID)
        for current_row_index in range(self.rowCount()):
            if current_row_index == row_index:
                continue
            current_index = self.index(current_row_index, 0, parent)
            current_id = self.data(current_index, TxListModel.Role.ID)
            if current_id == id_:
                if self.data(current_index, TxListModel.Role.VISIBLE):
                    return False

        # Note that you should not update the source model through the proxy
        # model when dynamicSortFilter is true.
        source_index = self.mapToSource(index)
        source_index.model().setData(
            source_index,
            True,
            TxListModel.Role.VISIBLE)
        return True


class TxListSortedModel(AbstractListSortedModel):
    def __init__(
            self,
            application: QmlApplication,
            source_model: TxListModel) -> None:
        super().__init__(
            application,
            source_model,
            TxListModel.Role.NAME,
            Qt.DescendingOrder)

    def filterAcceptsRow(
            self,
            source_row_index: int,
            source_parent: QModelIndex) -> bool:
        source_model = self.sourceModel()
        if isinstance(source_model, TxListConcatenateModel):
            return source_model.isVisibleRow(source_row_index, source_parent)
        return True

    def lessThan(
            self,
            source_left: QModelIndex,
            source_right: QModelIndex) -> bool:
        source_model = self.sourceModel()

        a = source_model.data(source_left, TxListModel.Role.STATE)
        b = source_model.data(source_right, TxListModel.Role.STATE)

        if a.height == -1 and b.height != -1:
            return False
        if a.height != -1 and b.height == -1:
            return True
        if a.height < b.height:
            return True
        if a.height > b.height:
            return False

        # TODO sort by server order

        if a.time < b.time:
            return True
        if a.time > b.time:
            return False

        a = source_model.data(source_left, TxListModel.Role.NAME)
        b = source_model.data(source_right, TxListModel.Role.NAME)
        return a < b
