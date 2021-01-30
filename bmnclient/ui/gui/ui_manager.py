from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Union, List, Type
from datetime import datetime
from PySide2.QtCore import \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot, \
    Property as QProperty, \
    QTimer

from ...ui.gui.system_tray import SystemTrayIcon, MessageIcon
from . import dialogs

if TYPE_CHECKING:
    from . import Application


log = logging.getLogger(__name__)


class UIManager(QObject):
    statusChanged = QSignal()
    visibleChanged = QSignal()
    statusMessageChanged = QSignal()
    outputInfo = QSignal(name="outputInfo", arguments=["key", "value"])
    serverVersionChanged = QSignal()
    hide = QSignal()
    show = QSignal()

    def __init__(self, application: Application) -> None:
        super().__init__()
        self._application = application
        self.__online = True
        self.__server_version = None
        self.__status_message = ""
        self.__visible = False
        #
        self.__notified_tx_list = set()
        #
        self.__tray = SystemTrayIcon(self)
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

    ############################################################################

    def process_incoming_tx(self, tx: Union['tx.Transaction', List['tx.Transaction']]):
        if isinstance(tx, list):
            for tx_ in tx:
                self.process_incoming_tx(tx_)
        else:
            # if: tx time more than launch time
            # and if: tx not already notified
            # don't detect direction !!!
            if tx.time >= self._launch_time.timestamp() and \
                    tx not in self.__notified_tx_list and \
                    True:
                self.__notified_tx_list.add(tx)
                log.info(f"NOTIFY ABOUT: {tx}")
                self.__tray.showMessage(
                    f"New transaction: {tx.user_view(self._application.settingsManager)}",
                    MessageIcon.INFORMATION,
                )

    def fill_coin_info_model(self, coin_map):
        for name, data in coin_map.items():
            remote = {}
            try:
                remote["version_string"] = str(data["version"][0])
                remote["version"] = int(data["version"][1])
            except (LookupError, TypeError, ValueError):
                remote["version_string"] = "unknown"
                remote["version"] = -1
            try:
                remote["height"] = int(data["height"])
            except (LookupError, TypeError, ValueError):
                remote["height"] = -1
            try:
                remote["status"] = int(data["status"])
            except (LookupError, TypeError, ValueError):
                remote["status"] = -1

            coin = self._application.findCoin(name)
            if coin is not None:
                coin._remote = remote
                coin.remoteStateModel.refresh()

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

    @QProperty(str, notify=serverVersionChanged)
    def serverVersion(self):
        return self.__server_version

    @serverVersion.setter
    def _set_server_version(self, vers):
        if vers == self.__server_version:
            return
        self.__server_version = vers
        self.serverVersionChanged.emit()

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
