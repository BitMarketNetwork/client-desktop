# JOK++
from __future__ import annotations

from enum import auto
from typing import TYPE_CHECKING

from PySide2.QtCore import QSignalMapper

from ..models import RoleEnum, AbstractListModel

if TYPE_CHECKING:
    from ..ui.gui import Application


class Role(RoleEnum):
    SHORT_NAME = auto()
    FULL_NAME = auto()
    ICON_PATH = auto()
    BALANCE = auto()
    FIAT_BALANCE = auto()
    UNIT = auto()
    TEST = auto()
    VISIBLE = auto()
    ENABLED = auto()
    ADDRESS_MODEL = auto()


class CoinListModel(AbstractListModel):
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

        Role.BALANCE: (
            b"balance",
            lambda c: c.balance),
        Role.FIAT_BALANCE: (
            b"fiatBalance",
            lambda c: c.fiatBalance),
        Role.UNIT: (
            b"unit",
            lambda c: c.unit),
        Role.TEST: (
            b"test",
            lambda c: c.test),
        Role.VISIBLE: (
            b"visible",
            lambda c: c.visible),
        Role.ENABLED: (
            b"enabled",
            lambda c: c.enabled),
        Role.ADDRESS_MODEL: (
            b"addressModel",
            lambda c: c.addressModel),
    }

    def __init__(self, application: Application) -> None:
        super().__init__(application.coinList)
        self._application = application

        self._signal_mapper = QSignalMapper()
        for i, c in enumerate(self._application.coinList):
            c.balanceChanged.connect(self._signal_mapper.map)
            self._signal_mapper.setMapping(c, i)
        self._signal_mapper.mapped.connect(self._onBalanceChanged)

    def _onBalanceChanged(self, index: int) -> None:
        self.dataChanged.emit(
            self.index(index),
            self.index(index),
            (Role.BALANCE, Role.FIAT_BALANCE))
