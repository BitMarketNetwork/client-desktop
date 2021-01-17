from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from PySide2.QtCore import \
    QObject, \
    Signal as QSignal

import PySide2.QtCore as qt_core
from ...wallet import key

if TYPE_CHECKING:
    from . import Application

log = logging.getLogger(__name__)


class ReceiveManager(QObject):
    addressChanged = QSignal(0)

    def __init__(self, application: Application) -> None:
        super().__init__()
        self._application = application
        self._address = None

    @qt_core.Property(str, notify=addressChanged)
    def address(self) -> str:
        if self._address:
            return self._address.name
        return ""

    @qt_core.Property(str, notify=addressChanged)
    def label(self) -> str:
        if self._address:
            return self._address.label
        return ""

    @qt_core.Property(str, notify=addressChanged)
    def message(self) -> str:
        if self._address:
            return self._address.message
        return ""

    @qt_core.Slot(bool, str, str)
    def accept(self, segwit: bool, label: str, message: str):
        _coin = self._application.coinManager.coin
        assert _coin
        self._address = _coin.make_address(
            key.AddressType.P2WPKH if segwit else key.AddressType.P2PKH,
            label,
            message,
         )
        self.addressChanged.emit()
