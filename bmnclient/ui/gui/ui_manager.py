from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Union, List, Type

from PySide2.QtCore import \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot, \
    Property as QProperty, \
    QTimer

from ...models import list_model, coin_daemon_model
from ...ui.gui.system_tray import SystemTrayIcon, MessageIcon

log = logging.getLogger(__name__)


class UIManager(QObject):
    statusChanged = QSignal()
    visibleChanged = QSignal()
    statusMessageChanged = QSignal()
    outputInfo = QSignal(name="outputInfo", arguments=["key", "value"])
    serverVersionChanged = QSignal()
    coinModelChanged = QSignal()
    coinIndexChanged = QSignal()
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
        self.__server_coin_model = list_model.ObjectListModel(self)
        self.__server_coin_index = 0
        self.__notified_tx_list = set()
        #
        self.__tray = SystemTrayIcon(self)
        self.__tray.exit.connect(self._application.setExitEvent)
        self.__tray.showMainWindow.connect(self.show)
        self.__tray.hideMainWindow.connect(self.hide)
        self.__tray.show()
        self.__notify_hidden = True

    def process_incoming_tx(self, tx: Union['tx.Transaction', List['tx.Transaction']]):
        if isinstance(tx, list):
            for tx_ in tx:
                self.process_incoming_tx(tx_)
        else:
            # if: tx time more than launch time
            # and if: tx not already notified
            # don't detect direction !!!
            # log.info(
            #     f"LAUNCH TIME:{self._application.gcd.launch_time} TX TIME:{tx.timeHuman}")
            if tx.time >= self._application.gcd.launch_time.timestamp() and \
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
            item = coin_daemon_model.CoinDaemonModel(self._application.gcd.coin(name), None, **data)
            item.moveToThread(self.__server_coin_model.thread())
            item.setParent(self.__server_coin_model)
            self.__server_coin_model.append(item)
        self.coinModelChanged.emit()

    @QProperty(QObject, notify=coinModelChanged)
    def coinInfoModel(self):
        return self.__server_coin_model

    @QProperty(int, notify=coinIndexChanged)
    def coinDaemonIndex(self):
        return self.__server_coin_index

    @QProperty(coin_daemon_model.CoinDaemonModel, notify=coinIndexChanged)
    def coinDaemon(self):
        if self.__server_coin_index < len(self.__server_coin_model._list):
            return self.__server_coin_model._list[self.__server_coin_index]

    @coinDaemonIndex.setter
    def _set_coin_index(self, index):
        if index == self.__server_coin_index:
            return
        self.__server_coin_index = index
        self.coinIndexChanged.emit()

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

    @QProperty(bool, constant=True)
    def dbValid(self) -> bool:
        return self._application.gcd.db_valid

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

    @QSlot()
    def resetDB(self) -> None:
        self._application.gcd.reset_db()
        self._application.keyStore.regenerate_master_key()
        self._application.gcd.coinManager.lookForHD()
