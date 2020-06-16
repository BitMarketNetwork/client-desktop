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
        self._online = True
        self._server_version = None
        self._terms_applied = False
        self._status_message = ""
        #
        self._server_coin_model = []
        self._server_coin_index = 0

    def fill_coin_info_model(self, coin_map):
        _gcd = self.parent().gcd
        for tag, data in coin_map.items():
            humanName = _gcd.get_coin_name(tag)
            ci = coin_info.CoinInfo(humanName, None, **data)
            ci.moveToThread(self.thread())
            ci.setParent(self)
            self._server_coin_model.append(ci)
        self.coinModelChanged.emit()

    @qt_core.Property('QStringList', notify=coinModelChanged)
    def coinInfoModel(self):
        return [coin.name for coin in self._server_coin_model]

    @qt_core.Property(int, notify=coinIndexChanged)
    def coinDaemonIndex(self):
        return self._server_coin_index

    @qt_core.Property(coin_info.CoinInfo, notify=coinIndexChanged)
    def coinDaemon(self):
        if self._server_coin_index < len(self._server_coin_model):
            return self._server_coin_model[self._server_coin_index]

    @coinDaemonIndex.setter
    def _set_coin_index(self, index):
        if index == self._server_coin_index:
            return
        self._server_coin_index = index
        self.coinIndexChanged.emit()

    @qt_core.Slot()
    def serverInfo(self):
        self.parent().serverInfo.emit()

    @qt_core.Property(bool, notify=statusChanged)
    def online(self):
        return self._online

    @qt_core.Property(str, notify=statusMessageChanged)
    def statusMessage(self):
        return self._status_message

    @online.setter
    def _set_online(self, on):
        if on == self._online:
            return
        self._online = on
        self.statusChanged.emit()

    @statusMessage.setter
    def _set_status_message(self, message):
        if message == self._status_message:
            return
        self._status_message = message
        qt_core.QTimer.singleShot(20000, self._reset_status)
        self.statusMessageChanged.emit()

    def _reset_status(self):
        self._status_message = ""
        self.statusMessageChanged.emit()

    @qt_core.Property(bool, notify=termsAppliedChanged)
    def termsApplied(self):
        return self._terms_applied

    @qt_core.Property(str, notify=serverVersionChanged)
    def serverVersion(self):
        return self._server_version

    @serverVersion.setter
    def _set_server_version(self, vers):
        if vers == self._server_version:
            return
        self._server_version = vers
        self.serverVersionChanged.emit()

    @termsApplied.setter
    def _set_terms_applied(self, tapp):
        if tapp == self._terms_applied:
            return
        if isinstance(tapp, str):
            log.debug(f"TOS and PP were applied by user already '{tapp}'")
            # assert "True" == tapp, tapp
            self._terms_applied = True
        else:
            log.debug(f"TOS and PP were applied by user right now {tapp}")
            self._terms_applied = tapp
            if tapp:
                self.parent().gcd.save_meta("terms", "True")
        self.termsAppliedChanged.emit()

    @qt_core.Slot(str)
    def copyToClipboard(self, text: str) -> None:
        import PySide2.QtGui as qt_gui
        log.debug(f"copying to clipboard: {text}")
        self.statusMessage = self.tr("Text '%s' copied to clipboard" % text)
        qt_gui.QGuiApplication.clipboard().setText(text)
