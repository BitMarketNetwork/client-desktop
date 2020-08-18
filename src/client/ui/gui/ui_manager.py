import logging

import PySide2.QtCore as qt_core
from client.wallet import coin_info

log = logging.getLogger(__name__)


class UIManager(qt_core.QObject):
    statusChanged = qt_core.Signal()
    statusMessageChanged = qt_core.Signal()
    showSpinner = qt_core.Signal(bool, arguments=["on"])
    outputInfo = qt_core.Signal(name="outputInfo", arguments=["key", "value"])
    serverVersionChanged = qt_core.Signal()
    termsAppliedChanged = qt_core.Signal()
    coinModelChanged = qt_core.Signal()
    coinIndexChanged = qt_core.Signal()

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.__online = True
        self.__server_version = None
        self.__terms_applied = False
        self.__status_message = ""
        #
        self.__server_coin_model = []
        self.__server_coin_index = 0

    @property
    def gcd(self) -> 'gcd.GCD':
        return self.parent().gcd

    def fill_coin_info_model(self, coin_map):
        for tag, data in coin_map.items():
            humanName = self.gcd.get_coin_name(tag)
            ci = coin_info.CoinInfo(humanName, None, **data)
            ci.moveToThread(self.thread())
            ci.setParent(self)
            self.__server_coin_model.append(ci)
        self.coinModelChanged.emit()

    @qt_core.Property('QStringList', notify=coinModelChanged)
    def coinInfoModel(self):
        return [coin.name for coin in self.__server_coin_model]

    @qt_core.Property(int, notify=coinIndexChanged)
    def coinDaemonIndex(self):
        return self.__server_coin_index

    @qt_core.Property(coin_info.CoinInfo, notify=coinIndexChanged)
    def coinDaemon(self):
        if self.__server_coin_index < len(self.__server_coin_model):
            return self.__server_coin_model[self.__server_coin_index]

    @coinDaemonIndex.setter
    def _set_coin_index(self, index):
        if index == self.__server_coin_index:
            return
        self.__server_coin_index = index
        self.coinIndexChanged.emit()

    @qt_core.Slot()
    def serverInfo(self):
        self.parent().serverInfo.emit()

    @qt_core.Property(bool, notify=statusChanged)
    def online(self):
        return self.__online

    @qt_core.Property(str, notify=statusMessageChanged)
    def statusMessage(self):
        return self.__status_message

    @online.setter
    def _set_online(self, on):
        if on == self.__online:
            return
        self.__online = on
        self.statusChanged.emit()

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

    @qt_core.Property(bool, notify=termsAppliedChanged)
    def termsApplied(self):
        # TODO: no web :()
        # return self.__terms_applied
        return True

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

    @termsApplied.setter
    def _set_terms_applied(self, tapp):
        if tapp == self.__terms_applied:
            return
        if isinstance(tapp, str):
            log.debug(f"TOS and PP were applied by user already '{tapp}'")
            # assert "True" == tapp, tapp
            self.__terms_applied = True
        else:
            log.debug(f"TOS and PP were applied by user right now {tapp}")
            self.__terms_applied = tapp
            if tapp:
                self.gcd.save_meta("terms", "True")
        self.termsAppliedChanged.emit()

    @qt_core.Slot(str)
    def copyToClipboard(self, text: str) -> None:
        import PySide2.QtGui as qt_gui
        log.debug(f"copying to clipboard: {text}")
        self.statusMessage = self.tr("Text '%s' copied to clipboard" % text)
        qt_gui.QGuiApplication.clipboard().setText(text)

    @qt_core.Slot()
    def resetDB(self) -> None:
        self.gcd.reset_db()
        self.parent().keyManager.regenerate_master_key()
        self.parent().coinManager.lookForHD()