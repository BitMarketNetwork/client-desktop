
import os
import logging
import functools
import PySide2.QtCore as qt_core
import PySide2.QtQml as qt_qml
# import PySide2.QtQuic as qt_quick
# import PySide2.QtGui as qt_gui
import PySide2.QtWidgets as qt_widgets
from . import ui_manager
from . import coin_manager
from . import settings_manager
from . import exchange_manager
from . import receive_manager
from client import debug_manager
from client import key_manager
from client import debug_manager
from client import key_manager
from client.wallet import coins
# linter
from client.wallet import base_unit
from client import ui

log = logging.getLogger(__name__)


class Api(qt_core.QObject):
    __instance = None
    updateTr = qt_core.Signal()

    def __init__(self, gcd):
        super().__init__(parent=gcd)
        self.__class__.__instance = self
        self._ui_manager = ui_manager.UIManager(self)
        self._settings_manager = settings_manager.SettingsManager(self)
        self._prev_language = None
        self._settings_manager.languageChanged.connect(
            #functools.partial(self.install_translator, self._settings_manager.language)
            self.install_translator
        )
        self._exchange_manager = exchange_manager.ExchangeManager(self)
        self._receive_manager = receive_manager.ReceiveManager(self)
        # there's no need to put it to queue but ...
        gcd.lockUI.connect(self._ui_manager.showSpinner,
                           qt_core.Qt.QueuedConnection)
        self._coin_api = coin_manager.CoinManager(gcd, self)
        gcd.netError.connect(self._on_network_error)
        self._tr = qt_core.QTranslator()

    @qt_core.Slot(int, str)
    def _on_network_error(self, code, error):
        self._ui_manager.online = 0 == code
        self._ui_manager.statusMessage = error
        if code != 0:
            log.error(f"Network error:{error} code:{code}")

    @classmethod
    def get_instance(cls):
        """
        we need singltone inside qml controllers ,
        because there's no way to access qml api inside.
        And moreover, we don't know when user instantiates them
        """
        return cls.__instance

    def _get_coin_manager(self) -> coin_manager.CoinManager:
        return self._coin_api

    def _get_ui_manager(self) -> ui_manager.UIManager:
        return self._ui_manager

    def _get_debug_manager(self) -> debug_manager.DebugManager:
        return self.parent().debug_man

    def _get_key_manager(self) -> key_manager.KeyManager:
        return self.parent().key_man

    def _get_settings_manager(self) -> settings_manager.SettingsManager:
        return self._settings_manager

    def _get_exchange_manager(self) -> exchange_manager.ExchangeManager:
        return self._exchange_manager

    def _get_receive_manager(self) -> receive_manager.ReceiveManager:
        return self._receive_manager

    def _debug_mode(self) -> bool:
        return ui.AppBase.debug_mode

    def show_spinner(self, on: bool):
        self._ui_manager.showSpinner.emit(on)

    @property
    def gcd(self) -> "GCD":
        return self.parent()

    @property
    def base_unit(self) -> base_unit.BaseUnit:
        return self._settings_manager.baseUnit


    coinManager = qt_core.Property(coin_manager.CoinManager,
                                   _get_coin_manager, constant=True)
    uiManager = qt_core.Property(ui_manager.UIManager,
                                 _get_ui_manager, constant=True)
    debugManager = qt_core.Property(debug_manager.DebugManager,
                                    _get_debug_manager, constant=True)
    keyManager = qt_core.Property(key_manager.KeyManager,
                                  _get_key_manager, constant=True)
    settingsManager = qt_core.Property(settings_manager.SettingsManager,
                                       _get_settings_manager, constant=True)
    exchangeManager = qt_core.Property(exchange_manager.ExchangeManager,
                                       _get_exchange_manager, constant=True)
    receiveManager = qt_core.Property(receive_manager.ReceiveManager,
                                      _get_receive_manager, constant=True)

    debugMode = qt_core.Property(bool, _debug_mode ,constant=True)

    def _install_translator(self, lang):
        # TODO: why qApp doesn't work on pyside14 ?
        app = qt_core.QCoreApplication.instance()
        if self._prev_language:
            app.removeTranslator(self._prev_language.py_translator)
            app.removeTranslator(self._prev_language.qml_translator)
        if app.installTranslator(lang.py_translator) and \
                app.installTranslator(lang.qml_translator):
            self.gcd.save_meta("language", lang.locale)
            self._prev_language = lang
            self.updateTr.emit()
        else:
            log.error(f"can't install tr:{lang.locale}")

    @qt_core.Slot()
    def install_translator(self):
        self._install_translator(self._settings_manager.language)