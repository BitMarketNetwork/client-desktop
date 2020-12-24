import logging
import functools
from typing import Union, List
from ...models import list_model, coin_daemon_model
import PySide2.QtCore as qt_core
from bmnclient.ui.gui.system_tray import SystemTrayIcon, MessageIcon

log = logging.getLogger(__name__)


class UIManager(qt_core.QObject):
    statusChanged = qt_core.Signal()
    visibleChanged = qt_core.Signal()
    statusMessageChanged = qt_core.Signal()
    outputInfo = qt_core.Signal(name="outputInfo", arguments=["key", "value"])
    serverVersionChanged = qt_core.Signal()
    coinModelChanged = qt_core.Signal()
    coinIndexChanged = qt_core.Signal()
    hide = qt_core.Signal()
    show = qt_core.Signal()

    def __init__(self, parent):
        super().__init__(parent=parent)
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
        self.__tray.quit.connect(
            functools.partial(self.gcd.quit, 0)
        )
        self.__tray.showMainWindow.connect(self.show)
        self.__tray.hideMainWindow.connect(self.hide)
        self.__tray.show()
        self.__notify_hidden = True

    @property
    def gcd(self) -> 'gcd.GCD':
        return self.parent().gcd

    def process_incoming_tx(self, tx: Union['tx.Transaction', List['tx.Transaction']]):
        if isinstance(tx, list):
            for tx_ in tx:
                self.process_incoming_tx(tx_)
        else:
            # if: tx time more than launch time
            # and if: tx not already notified
            # don't detect direction !!!
            # log.info(
            #     f"LAUNCH TIME:{self.gcd.launch_time} TX TIME:{tx.timeHuman}")
            if tx.time >= self.gcd.launch_time.timestamp() and \
                    tx not in self.__notified_tx_list and \
                    True:
                self.__notified_tx_list.add(tx)
                log.info(f"NOTIFY ABOUT: {tx}")
                self.__tray.showMessage(
                    f"New transaction: {tx.user_view(self.parent().settingsManager)}",
                    MessageIcon.INFORMATION,
                )

    def fill_coin_info_model(self, coin_map):
        for name, data in coin_map.items():
            item = coin_daemon_model.CoinDaemonModel(self.gcd.coin(name), None, **data)
            item.moveToThread(self.__server_coin_model.thread())
            item.setParent(self.__server_coin_model)
            self.__server_coin_model.append(item)
        self.coinModelChanged.emit()

    @qt_core.Property(qt_core.QObject, notify=coinModelChanged)
    def coinInfoModel(self):
        return self.__server_coin_model

    @qt_core.Property(int, notify=coinIndexChanged)
    def coinDaemonIndex(self):
        return self.__server_coin_index

    @qt_core.Property(coin_daemon_model.CoinDaemonModel, notify=coinIndexChanged)
    def coinDaemon(self):
        if self.__server_coin_index < len(self.__server_coin_model._list):
            return self.__server_coin_model._list[self.__server_coin_index]

    @coinDaemonIndex.setter
    def _set_coin_index(self, index):
        if index == self.__server_coin_index:
            return
        self.__server_coin_index = index
        self.coinIndexChanged.emit()

    @qt_core.Property(bool, notify=statusChanged)
    def online(self):
        return self.__online

    @qt_core.Property(bool, notify=visibleChanged)
    def visible(self):
        return self.__visible

    @qt_core.Property(str, notify=statusMessageChanged)
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
        qt_core.QTimer.singleShot(20000, self._reset_status)
        self.statusMessageChanged.emit()

    def _reset_status(self):
        self.__status_message = ""
        self.statusMessageChanged.emit()

    @qt_core.Property(str, notify=serverVersionChanged)
    def serverVersion(self):
        return self.__server_version

    @qt_core.Property(bool, constant=True)
    def dbValid(self) -> bool:
        return self.gcd.db_valid

    @serverVersion.setter
    def _set_server_version(self, vers):
        if vers == self.__server_version:
            return
        self.__server_version = vers
        self.serverVersionChanged.emit()

    @qt_core.Slot(str)
    def copyToClipboard(self, text: str) -> None:
        import PySide2.QtGui as qt_gui
        log.debug(f"copying to clipboard: {text}")
        self.statusMessage = self.tr("Text '%s' copied to clipboard" % text)
        qt_gui.QGuiApplication.clipboard().setText(text)

    @qt_core.Slot(str, int)
    def notify(self, message: str, level: int = MessageIcon.INFORMATION):
        self.__tray.showMessage(message, level)

    @qt_core.Slot()
    def resetDB(self) -> None:
        self.gcd.reset_db()
        self.parent().keyManager.regenerate_master_key()
        self.parent().coinManager.lookForHD()
