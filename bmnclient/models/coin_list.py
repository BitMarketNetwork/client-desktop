# JOK++
from __future__ import annotations

from enum import auto
from typing import TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    Signal as QSignal

from . import RoleEnum, AbstractListModel, AbstractStateModel

if TYPE_CHECKING:
    from ..ui.gui import Application
    from ..wallet.coins import CoinType


class AbstractCoinStateModel(AbstractStateModel):
    def __init__(self, coin: CoinType) -> None:
        super().__init__()
        self._coin = coin


class StateModel(AbstractCoinStateModel):
    _stateChanged = QSignal()

    @QProperty(bool, notify=_stateChanged)
    def visible(self) -> bool:
        return self._coin.visible

    @visible.setter
    def _setVisible(self, value) -> None:
        self._coin.visible = value


class RemoteStateModel(AbstractCoinStateModel):
    _stateChanged = QSignal()

    @QProperty(str, notify=_stateChanged)
    def humanVersion(self) -> str:
        return self._coin._remote.get("version_string", "-")  # TODO

    @QProperty(int, notify=_stateChanged)
    def version(self) -> int:
        return self._coin._remote.get("version", -1)  # TODO

    @QProperty(int, notify=_stateChanged)
    def status(self) -> int:
        return self._coin._remote.get("status", -1)  # TODO

    @QProperty(int, notify=_stateChanged)
    def height(self) -> int:
        return self._coin._remote.get("height", -1)  # TODO


class AmountModel(AbstractCoinStateModel):
    _stateChanged = QSignal()

    @QProperty(str, notify=_stateChanged)
    def valueHuman(self) -> str:
        return self._coin.amountToString(self._coin.balance)

    @QProperty(str, constant=True)
    def unit(self) -> str:
        return self._coin.unit

    @QProperty(str, notify=_stateChanged)
    def fiatValueHuman(self) -> str:
        return str(self._coin.fiatBalance)

    @QProperty(str, notify=_stateChanged)
    def fiatUnit(self) -> str:
        return "USD"


class CoinListModel(AbstractListModel):
    class Role(RoleEnum):
        SHORT_NAME = auto()
        FULL_NAME = auto()
        ICON_PATH = auto()
        AMOUNT = auto()
        STATE = auto()
        REMOTE_STATE = auto()
        ADDRESS_MODEL = auto()

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

        Role.ADDRESS_MODEL: (
            b"addressModel",
            lambda c: c.addressModel),
    }

    def __init__(self, application: Application) -> None:
        super().__init__(application.coinList)
        self._application = application
