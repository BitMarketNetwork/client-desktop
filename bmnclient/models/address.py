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


class AddressModel(AbstractModel):
    def __init__(self, application: Application, address: CAddress) -> None:
        super().__init__(application, address)
        self._address = address


class AddressListModel(AbstractListModel):
    class Role(RoleEnum):
        NAME: Final = auto()
        AMOUNT: Final = auto()
        STATE: Final = auto()
        TX_LIST: Final = auto()

    ROLE_MAP: Final = {
        Role.NAME: (
            b"name",
            lambda a: a.name),
        Role.AMOUNT: (
            b"amount",
            lambda a: a.amountModel),
        Role.STATE: (
            b"state",
            lambda a: a.stateModel),
        Role.TX_LIST: (
            b"txList",
            lambda a: a.txListSortedModel)
    }


class AddressListSortedModel(AbstractListSortedModel):
    def __init__(
            self,
            application: Application,
            source_model: AddressListModel) -> None:
        super().__init__(application, source_model, AddressListModel.Role.NAME)
