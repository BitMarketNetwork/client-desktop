# JOK++
from __future__ import annotations

from enum import auto

from PySide2.QtCore import \
    Property as QProperty, \
    Signal as QSignal

from . import \
    AbstractAmountModel, \
    AbstractListModel, \
    AbstractCoinStateModel, \
    RoleEnum


class CoinStateModel(AbstractCoinStateModel):
    _stateChanged = QSignal()

    @QProperty(bool, notify=_stateChanged)
    def visible(self) -> bool:
        return self._coin.visible

    @visible.setter
    def _setVisible(self, value) -> None:
        self._coin.visible = value


class CoinRemoteStateModel(AbstractCoinStateModel):
    _stateChanged = QSignal()

    @QProperty(str, notify=_stateChanged)
    def versionHuman(self) -> str:
        # noinspection PyProtectedMember
        return self._coin._remote.get("version_string", "-")  # TODO

    @QProperty(int, notify=_stateChanged)
    def version(self) -> int:
        # noinspection PyProtectedMember
        return self._coin._remote.get("version", -1)  # TODO

    @QProperty(int, notify=_stateChanged)
    def status(self) -> int:
        # noinspection PyProtectedMember
        return self._coin._remote.get("status", -1)  # TODO

    @QProperty(int, notify=_stateChanged)
    def height(self) -> int:
        # noinspection PyProtectedMember
        return self._coin._remote.get("height", -1)  # TODO

    @QProperty(str, notify=_stateChanged)
    def heightHuman(self) -> str:
        height = self.height
        if height < 0:
            return "-"
        return self._application.language.locale.integerToString(height)


class CoinAmountModel(AbstractAmountModel, AbstractCoinStateModel):
    def _value(self) -> int:
        return self._coin.balance

    def _fiatValue(self) -> float:
        return self._coin.fiatBalance


class CoinListModel(AbstractListModel):
    class Role(RoleEnum):
        SHORT_NAME = auto()
        FULL_NAME = auto()
        ICON_PATH = auto()
        AMOUNT = auto()
        STATE = auto()
        REMOTE_STATE = auto()
        ADDRESS_LIST = auto()
        TX_LIST = auto()

    _ROLE_MAP = {
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
