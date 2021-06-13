from __future__ import annotations

import logging
from datetime import datetime
from typing import Type, TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, QTimer, \
    Signal as QSignal, \
    Slot as QSlot

from . import dialogs
from .models.tx import TxModel
from ...ui.gui.system_tray import MessageIcon, SystemTrayIcon

if TYPE_CHECKING:
    from . import GuiApplication
    from ...coins.abstract.coin import AbstractCoin


log = logging.getLogger(__name__)


class UIManager(QObject):
    statusChanged = QSignal()
    visibleChanged = QSignal()
    statusMessageChanged = QSignal()
    outputInfo = QSignal(name="outputInfo", arguments=["key", "value"])
    hide = QSignal()
    show = QSignal()

    def __init__(self, application: GuiApplication) -> None:
        super().__init__()
        self._application = application
        self.__online = True
        self.__status_message = ""
        self.__visible = False
        #
        self.__notified_tx_list = []
        #
        self.__tray = SystemTrayIcon(self._application)
        self.__tray.exit.connect(self._application.setExitEvent)
        self.__tray.showMainWindow.connect(self.show)
        self.__tray.hideMainWindow.connect(self.hide)
        self.__tray.show()
        self.__notify_hidden = True
        self._launch_time = datetime.utcnow()

    @QSlot()
    def onMainComponentCompleted(self) -> None:
        self.openDialog(dialogs.BAlphaDialog)

    ############################################################################
    # Dialogs
    ############################################################################

    openDialogSignal = QSignal(str, "QVariantMap")

    def openDialog(self, dialog: Type[dialogs.Dialog]) -> None:
        properties = {
            "signals": []
        }
        for n in dir(dialog):
            if n.startswith("on") and callable(getattr(dialog, n)):
                properties["signals"].append(n)
        self.openDialogSignal.emit(dialog.__name__, properties)

    @QSlot(str, str)
    def onDialogSignal(self, name: str, signal: str) -> None:
        dialog = getattr(dialogs, name)(self._application.backendContext)
        getattr(dialog, signal)()

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

    @QProperty(bool, notify=statusChanged)
    def online(self):
        return self.__online

    @QProperty(bool, notify=visibleChanged)
    def visible(self):
        return self.__visible

    @QProperty(str, notify=statusMessageChanged)
    def statusMessage(self):
        return self.__status_message

    @online.setter
    def _set_online(self, on):
        if on == self.__online:
            return
        self.__online = on
        self.statusChanged.emit()

    @visible.setter
    def _set_visible(self, on):
        if on == self.__visible:
            return
        self.__visible = on
        self.__tray.setMainWindowVisibleState(on)
        self.visibleChanged.emit()

    @statusMessage.setter
    def _set_status_message(self, message):
        if not message or message == self.__status_message:
            return
        self.__status_message = message
        QTimer.singleShot(20000, self._reset_status)
        self.statusMessageChanged.emit()

    def _reset_status(self):
        self.__status_message = ""
        self.statusMessageChanged.emit()

    @QProperty(str, constant=True)
    def title(self) -> str:
        return self._application.title

    @QSlot(str)
    def copyToClipboard(self, text: str) -> None:
        import PySide2.QtGui as qt_gui
        log.debug(f"copying to clipboard: {text}")
        self.statusMessage = self.tr("Text '%s' copied to clipboard" % text)
        qt_gui.QGuiApplication.clipboard().setText(text)

    @QSlot(str, int)
    def notify(self, message: str, level: int = MessageIcon.INFORMATION):
        self.__tray.showMessage(message, level)

    @QSlot(int)
    def exit(self, code: int) -> None:
        self._application.setExitEvent(code)
