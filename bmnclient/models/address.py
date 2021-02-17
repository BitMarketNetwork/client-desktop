# JOK++
from __future__ import annotations

from enum import auto
from typing import Final, Optional, TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    Signal as QSignal

from . import AbstractModel, AbstractStateModel
from .amount import AmountModel
from .list import \
    AbstractListModel, \
    AbstractListSortedModel, \
    RoleEnum

if TYPE_CHECKING:
    from ..ui.gui import Application
    from ..wallet.address import CAddress


class AbstractAddressStateModel(AbstractStateModel):
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


class AddressAmountModel(AmountModel):
    def __init__(self, application: Application, address: CAddress) -> None:
        super().__init__(application, address.coin)
        self._address = address

    def _getValue(self) -> Optional[int]:
        return self._address.balance


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


class AddressModel(AbstractModel):
    # TODO
    pass
