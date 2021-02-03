# JOK++
from __future__ import annotations

from enum import auto

from PySide2.QtCore import \
    Property as QProperty, \
    Signal as QSignal

from . import \
    AbstractAddressStateModel, \
    AbstractAmountModel, \
    AbstractListModel, \
    AbstractListSortedModel, \
    RoleEnum


class AddressStateModel(AbstractAddressStateModel):
    _stateChanged = QSignal()

    @QProperty(str, notify=_stateChanged)
    def label(self) -> str:
        return self._address.label

    @QProperty(bool, constant=True)
    def watchOnly(self) -> bool:
        return self._address.readOnly

    @QProperty(bool, notify=_stateChanged)
    def isUpdating(self) -> bool:
        return self._address.isUpdating


class AddressAmountModel(AbstractAmountModel, AbstractAddressStateModel):
    def _value(self) -> int:
        return self._address.balance

    def _fiatValue(self) -> float:
        return self._address.fiatBalance


class AddressListModel(AbstractListModel):
    class Role(RoleEnum):
        COIN = auto()
        NAME = auto()
        AMOUNT = auto()
        STATE = auto()
        TX_LIST = auto()

    _ROLE_MAP = {
        Role.COIN: (
            b"coin",
            lambda a: a.coin),
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
    def __init__(self, source_model: AddressListModel) -> None:
        super().__init__(source_model, AddressListModel.Role.NAME)
