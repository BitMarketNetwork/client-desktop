from __future__ import annotations

from typing import TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot

from .models.tx import TxModel
from ...ui.gui.system_tray import MessageIcon, SystemTrayIcon

if TYPE_CHECKING:
    from . import GuiApplication
    from ...coins.abstract.coin import AbstractCoin


class UIManager(QObject):
    visibleChanged = QSignal()
    hide = QSignal()
    show = QSignal()

    def __init__(self, application: GuiApplication) -> None:
        super().__init__()
        self._application = application
        self.__visible = False
        #
        self.__notified_tx_list = []
        #
        self.__tray = SystemTrayIcon(self._application)
        self.__tray.exit.connect(self._application.setExitEvent)
        self.__tray.showMainWindow.connect(self.show)
        self.__tray.hideMainWindow.connect(self.hide)
        self.__tray.show()

    def process_incoming_tx(self, tx: AbstractCoin.Tx) -> None:
        if tx.rowId is not None:
            return
        if tx.name in self.__notified_tx_list:
            return
        self.__notified_tx_list.append(tx.name)

        tx_model = tx.model
        if not isinstance(tx_model, TxModel):
            return

        # noinspection PyTypeChecker
        message = self.tr(
            "New transaction\n"
            "Coin: {coin_name}\n"
            "ID: {tx_name}\n"
            "Amount: {amount} {unit} / {fiat_amount} {fiat_unit}")
        message = message.format(
            coin_name=tx.coin.fullName,
            tx_name=tx_model.name,
            amount=tx_model.amount.valueHuman,
            unit=tx_model.amount.unit,
            fiat_amount=tx_model.amount.fiatValueHuman,
            fiat_unit=tx_model.amount.fiatUnit)
        self.__tray.showMessage(message, MessageIcon.INFORMATION)

    @QProperty(bool, notify=visibleChanged)
    def visible(self):
        return self.__visible

    @visible.setter
    def _set_visible(self, on):
        if on == self.__visible:
            return
        self.__visible = on
        self.__tray.setMainWindowVisibleState(on)
        self.visibleChanged.emit()

    @QProperty(str, constant=True)
    def title(self) -> str:
        return self._application.title

    @QSlot(str)
    def copyToClipboard(self, text: str) -> None:
        import PySide2.QtGui as qt_gui
        qt_gui.QGuiApplication.clipboard().setText(text)

    @QSlot(str, int)
    def notify(self, message: str, level: int = MessageIcon.INFORMATION):
        self.__tray.showMessage(message, level)

    @QSlot(int)
    def exit(self, code: int) -> None:
        self._application.setExitEvent(code)
