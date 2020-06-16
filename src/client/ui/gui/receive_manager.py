
import logging

import PySide2.QtCore as qt_core
import PySide2.QtGui as qt_gui
from . import api
from ...wallet import key
log = logging.getLogger(__name__)


class ReceiveManager(qt_core.QObject):
    addressChanged = qt_core.Signal(0)

    def __init__(self, parent):
        super().__init__(parent)
        self._clipb = qt_gui.QGuiApplication.clipboard()
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
        _coin = self.parent().coinManager.coin
        assert _coin
        self._address = _coin.make_address( 
            key.AddressType.P2WPKH if segwit else key.AddressType.P2PKH,
            label,
            message,
         )
        self.addressChanged.emit()

    @qt_core.Slot()
    def toClipboard(self):
        self._clipb.setText(self.address)
