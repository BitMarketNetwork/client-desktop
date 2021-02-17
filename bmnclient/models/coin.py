# JOK++
from __future__ import annotations

from enum import auto
from typing import Final

from PySide2.QtCore import \
    Property as QProperty, \
    Signal as QSignal

from . import AbstractModel, AbstractStateModel
from .amount import AmountModel
from .list import \
    AbstractListModel, \
    RoleEnum


class CoinStateModel(AbstractStateModel):
    __stateChanged = QSignal()

    @QProperty(bool, notify=__stateChanged)
    def visible(self) -> bool:
        return self._coin.visible

    @visible.setter
    def _setVisible(self, value) -> None:
        self._coin.visible = value


class CoinRemoteStateModel(AbstractStateModel):
    __stateChanged = QSignal()

    @QProperty(str, notify=__stateChanged)
    def versionHuman(self) -> str:
        # noinspection PyProtectedMember
        return self._coin._remote.get("version_string", "-")  # TODO

    @QProperty(int, notify=__stateChanged)
    def version(self) -> int:
        # noinspection PyProtectedMember
        return self._coin._remote.get("version", -1)  # TODO

    @QProperty(int, notify=__stateChanged)
    def status(self) -> int:
        # noinspection PyProtectedMember
        return self._coin._remote.get("status", -1)  # TODO

    @QProperty(int, notify=__stateChanged)
    def height(self) -> int:
        # noinspection PyProtectedMember
        return self._coin._remote.get("height", -1)  # TODO

    @QProperty(str, notify=__stateChanged)
    def heightHuman(self) -> str:
        height = self.height
        if height < 0:
            return "-"
        return self.locale.integerToString(height)


class CoinAmountModel(AmountModel):
    def _getValue(self) -> int:
        return self._coin.amount


class CoinListModel(AbstractListModel):
    class Role(RoleEnum):
        SHORT_NAME: Final = auto()
        FULL_NAME: Final = auto()
        ICON_PATH: Final = auto()
        AMOUNT: Final = auto()
        STATE: Final = auto()
        REMOTE_STATE: Final = auto()
        ADDRESS_LIST: Final = auto()
        TX_LIST: Final = auto()

    ROLE_MAP: Final = {
        Role.SHORT_NAME: (
            b"shortName",
            lambda c: c.shortName),
        Role.FULL_NAME: (
            b"fullName",
            lambda c: c.fullName),
        Role.ICON_PATH: (
            b"iconPath",
            lambda c: c.iconPath),
        Role.AMOUNT: (
            b"amount",
            lambda c: c.amountModel),
        Role.STATE: (
            b"state",
            lambda c: c.stateModel),
        Role.REMOTE_STATE: (
            b"remoteState",
            lambda c: c.remoteStateModel),
        Role.ADDRESS_LIST: (
            b"addressList",
            lambda c: c.addressListSortedModel()),
        Role.TX_LIST: (
            b"txList",
            lambda c: c.txListSortedModel())
    }


class CoinModel(AbstractModel):
    # TODO
    pass
