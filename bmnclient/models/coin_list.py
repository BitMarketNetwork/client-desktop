# JOK++
from __future__ import annotations

from enum import auto
from typing import TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal

from ..models import RoleEnum, AbstractListModel

if TYPE_CHECKING:
    from ..ui.gui import Application
    from ..wallet.coins import CoinType


class StateModel(QObject):
    _stateChanged = QSignal()

    def __init__(self, coin: CoinType) -> None:
        super().__init__()
        self._coin = coin

    @QProperty(bool, notify=_stateChanged)
    def visible(self) -> bool:
        return self._coin.visible

    @visible.setter
    def _setVisible(self, value) -> None:
        self._coin.visible = value

    def refresh(self) -> None:
        self._stateChanged.emit()


class AmountModel(QObject):
    _amountChanged = QSignal()

    def __init__(self, coin: CoinType) -> None:
        super().__init__()
        self._coin = coin

    @QProperty(str, notify=_amountChanged)
    def valueHuman(self) -> str:
        return self._coin.amountToString(self._coin.balance)

    @QProperty(str, constant=True)
    def unit(self) -> str:
        return self._coin.unit

    @QProperty(str, notify=_amountChanged)
    def fiatValueHuman(self) -> str:
        return str(self._coin.fiatBalance)

    @QProperty(str, notify=_amountChanged)
    def fiatUnit(self) -> str:
        return "USD"

    def refresh(self) -> None:
        self._amountChanged.emit()


class CoinListModel(AbstractListModel):
    class Role(RoleEnum):
        SHORT_NAME = auto()
        FULL_NAME = auto()
        ICON_PATH = auto()
        AMOUNT = auto()
        STATE = auto()
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

        Role.ADDRESS_MODEL: (
            b"addressModel",
            lambda c: c.addressModel),
    }

    def __init__(self, application: Application) -> None:
        super().__init__(application.coinList)
        self._application = application
