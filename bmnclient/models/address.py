# JOK4
from __future__ import annotations

from enum import auto
from typing import TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot

from . import AbstractModel, AbstractStateModel
from .amount import AbstractAmountModel
from .list import \
    AbstractListModel, \
    AbstractListSortedModel, \
    RoleEnum
from ..coin_interfaces import AddressInterface

if TYPE_CHECKING:
    from typing import Final, Optional
    from .tx import TxListModel, TxListSortedModel
    from ..coins.abstract.coin import AbstractCoin
    from ..ui.gui import GuiApplication


class AbstractAddressStateModel(AbstractStateModel):
    def __init__(
            self,
            application: GuiApplication,
            address: AbstractCoin.Address) -> None:
        super().__init__(application, address.coin)
        self._address = address


class AbstractAddressAmountModel(AbstractAmountModel):
    def __init__(
            self,
            application: GuiApplication,
            address: AbstractCoin.Address) -> None:
        super().__init__(application, address.coin)
        self._address = address

    def _getValue(self) -> Optional[int]:
        raise NotImplementedError


class AddressStateModel(AbstractAddressStateModel):
    __stateChanged = QSignal()

    @QProperty(str, notify=__stateChanged)
    def label(self) -> str:
        return self._address.label

    @QProperty(bool, constant=True)
    def isReadOnly(self) -> bool:
        return self._address.isReadOnly

    @QProperty(bool, notify=__stateChanged)
    def isUpdating(self) -> bool:
        return False  # TODO self._address.isUpdating

    @QProperty(bool, notify=__stateChanged)
    def useAsTransactionInput(self) -> bool:
        pass
        # TODO
        # return self._address.useAsSource

    @useAsTransactionInput.setter
    def _setUseAsTransactionInput(self, value: bool):
        # TODO
        # if self._address.useAsSource != value:
        #     self._address.useAsSource = value
        #     self.refresh()
        pass


class AddressAmountModel(AbstractAddressAmountModel):
    def refresh(self) -> None:
        super().refresh()
        for tx in self._address.txList:
            # noinspection PyUnresolvedReferences
            tx.model.amount.refresh()
            # noinspection PyUnresolvedReferences
            tx.model.feeAmount.refresh()

    def _getValue(self) -> Optional[int]:
        return self._address.amount


class AddressModel(AddressInterface, AbstractModel):
    def __init__(
            self,
            application: GuiApplication,
            address: AbstractCoin.Address) -> None:
        super().__init__(
            application,
            query_scheduler=application.networkQueryScheduler,
            database=application.database,
            address=address)

        self._amount_model = AddressAmountModel(
            self._application,
            self._address)
        self.connectModelRefresh(self._amount_model)

        self._state_model = AddressStateModel(
            self._application,
            self._address)
        self.connectModelRefresh(self._state_model)

        from .tx import TxListModel
        self._tx_list_model = TxListModel(
            self._application,
            self._address.txList)

    @QProperty(str, constant=True)
    def name(self) -> str:
        return self._address.name

    @QProperty(QObject, constant=True)
    def amount(self) -> AddressAmountModel:
        return self._amount_model

    @QProperty(QObject, constant=True)
    def state(self) -> AddressStateModel:
        return self._state_model

    @QProperty(QObject, constant=True)
    def txList(self) -> TxListModel:
        return self._tx_list_model

    # noinspection PyTypeChecker
    @QSlot(result=QObject)
    def txListSorted(self) -> TxListSortedModel:
        from .tx import TxListSortedModel
        return TxListSortedModel(
            self._application,
            self._tx_list_model)

    def afterSetAmount(self) -> None:
        self._amount_model.refresh()
        super().afterSetAmount()

    def afterSetLabel(self) -> None:
        self._state_model.refresh()
        super().afterSetLabel()

    def afterSetComment(self) -> None:
        self._state_model.refresh()
        super().afterSetComment()

    def afterSetTxCount(self) -> None:
        super().afterSetTxCount()

    def beforeAppendTx(self, tx: AbstractCoin.Tx) -> None:
        self._tx_list_model.lock(self._tx_list_model.lockInsertRows())
        super().beforeAppendTx(tx)

    def afterAppendTx(self, tx: AbstractCoin.Tx) -> None:
        self._tx_list_model.unlock()
        super().afterAppendTx(tx)
        self._application.uiManager.process_incoming_tx(tx)


class AddressListModel(AbstractListModel):
    class Role(RoleEnum):
        NAME: Final = auto()
        AMOUNT: Final = auto()
        STATE: Final = auto()
        TX_LIST: Final = auto()

    ROLE_MAP: Final = {
        Role.NAME: (
            b"name",
            lambda a: a.model.name),
        Role.AMOUNT: (
            b"amount",
            lambda a: a.model.amount),
        Role.STATE: (
            b"state",
            lambda a: a.model.state),
        Role.TX_LIST: (
            b"txList",
            lambda a: a.model.txListSorted)
    }


class AddressListSortedModel(AbstractListSortedModel):
    def __init__(
            self,
            application: GuiApplication,
            source_model: AddressListModel) -> None:
        super().__init__(application, source_model, AddressListModel.Role.NAME)
