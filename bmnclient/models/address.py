# JOK++
from __future__ import annotations

from abc import ABCMeta
from enum import auto
from typing import Final, Optional, TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot

from . import AbstractModel, AbstractStateModel
from .amount import AmountModel
from .list import \
    AbstractListModel, \
    AbstractListSortedModel, \
    RoleEnum
from ..coins.address import AddressModelInterface

if TYPE_CHECKING:
    from .tx import TxListModel, TxListSortedModel
    from ..ui.gui import Application
    from ..wallet.address import CAddress
    from ..wallet.tx import Transaction


class AbstractAddressStateModel(AbstractStateModel):
    def __init__(self, application: Application, address: CAddress) -> None:
        super().__init__(application, address.coin)
        self._address = address


class AbstractAddressAmountModel(AmountModel, metaclass=ABCMeta):
    def __init__(self, application: Application, address: CAddress) -> None:
        super().__init__(application, address.coin)
        self._address = address


class AddressStateModel(AbstractAddressStateModel):
    __stateChanged = QSignal()

    @QProperty(str, notify=__stateChanged)
    def label(self) -> str:
        return self._address.label

    @QProperty(bool, constant=True)
    def watchOnly(self) -> bool:
        return self._address.readOnly

    @QProperty(bool, notify=__stateChanged)
    def isUpdating(self) -> bool:
        return self._address.isUpdating

    @QProperty(bool, notify=__stateChanged)
    def useAsTransactionInput(self) -> bool:
        return self._address.useAsSource

    @useAsTransactionInput.setter
    def _setUseAsTransactionInput(self, value: bool):
        if self._address.useAsSource != value:
            self._address.useAsSource = value
            self.refresh()


class AddressAmountModel(AbstractAddressAmountModel):
    def _getValue(self) -> Optional[int]:
        return self._address.balance


class AddressModel(AddressModelInterface, AbstractModel):
    def __init__(self, application: Application, address: CAddress) -> None:
        super().__init__(application)
        self._address = address

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

    def beforeAppendTx(self, tx: Transaction) -> None:
        self._tx_list_model.lock(self._tx_list_model.lockInsertRows())

    def afterAppendTx(self, tx: Transaction) -> None:
        self._tx_list_model.unlock()


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
            application: Application,
            source_model: AddressListModel) -> None:
        super().__init__(application, source_model, AddressListModel.Role.NAME)
