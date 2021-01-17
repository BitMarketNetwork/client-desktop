from __future__ import annotations
import logging

from PySide2 import QtCore, QtQml, QtWidgets, QtQuickControls2
from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QFont

import bmnclient.version
from bmnclient.gcd import GCD
from bmnclient.meta import override
from ...application import CoreApplication
from . import qml_context, tx_controller, ui_manager, \
    receive_manager, coin_manager, settings_manager
from .coin_manager import CoinManager
from .qml_context import BackendContext
from .receive_manager import ReceiveManager
from .settings_manager import SettingsManager
from .ui_manager import UIManager
from ...server.network_factory import NetworkFactory
from ...language import Language

log = logging.getLogger(__name__)

QML_STYLE = "Material"
QML_FILE = "main.qml"
QML_CONTEXT_NAME = "BBackend"


class Application(CoreApplication):
    def __init__(self, argv) -> None:
        super().__init__(QApplication, argv)

        # TODO kill
        self.gcd = GCD(silent_mode=bmnclient.command_line.silent_mode())
        self.gcd.netError.connect(self._on_network_error)

        self._initializeManagers()
        self._initializeQml()

        # TODO kill
        self.gcd.updateTxStatus.connect(
                self._coin_manager.update_tx,
                QtCore.Qt.QueuedConnection)

    def _initializeManagers(self) -> None:
        self._settings_manager = SettingsManager(self._user_config)
        self._ui_manager = UIManager(self, self)
        self._receive_manager = ReceiveManager(self)
        self._coin_manager = CoinManager(self.gcd, self)

        self._settings_manager.currentLanguageNameChanged.connect(
            self._updateLanguage)

    def _initializeQml(self) -> None:
        QtQuickControls2.QQuickStyle.setStyle(QML_STYLE)
        log.debug("QML Base URL: %s", bmnclient.resources.QML_URL)

        self._backend_context = BackendContext(self, self.gcd)
        self._qml_network_factory = NetworkFactory(self)

        self._qml_engine = QtQml.QQmlApplicationEngine(self)
        # TODO self._engine.offlineStoragePath
        self._qml_engine.setBaseUrl(bmnclient.resources.QML_URL)
        self._qml_engine.setNetworkAccessManagerFactory(
            self._qml_network_factory)
        # TODO replace with self._engine.warnings
        self._qml_engine.setOutputWarningsToStandardError(True)

        qml_root_context = self._qml_engine.rootContext()
        qml_root_context.setBaseUrl(bmnclient.resources.QML_URL)
        qml_root_context.setContextProperty(
            QML_CONTEXT_NAME,
            self._backend_context)

        # TODO kill
        QtQml.qmlRegisterType(
            tx_controller.TxController,
            "Bmn",
            1, 0,
            "TxController")

        self._qml_engine.objectCreated.connect(self._onQmlObjectCreated)
        # TODO self._qml_engine.warnings.connect(self._onQmlWarnings)
        self._qml_engine.exit.connect(self._onQmlExit)

    @classmethod
    def instance(cls) -> Application:
        return super().instance()

    @property
    def defaultFont(self) -> QFont:
        return self._qt_application.font()

    @property
    def backendContext(self) -> BackendContext:
        return self._backend_context

    @override
    def _onRun(self) -> None:
        super()._onRun()
        self.gcd.start_threads()
        url = self._qml_engine.rootContext().resolvedUrl(QtCore.QUrl(QML_FILE))
        self._updateLanguage()
        self._qml_engine.load(url)

    @QtCore.Slot(QtCore.QObject, QtCore.QUrl)
    def _onQmlObjectCreated(self, qml_object, url) -> None:
        if qml_object is None:
            # TODO If an error occurs, the objectCreated signal is emitted with
            #  a null pointer as parameter an
            self.setQuitEvent()
        else:
            log.debug(f"QML object was created: {url.toString()}")

    @QtCore.Slot(list)
    def _onQmlWarnings(self, warning_list) -> None:
        # TODO: TypeError: Can't call meta function because I have no idea how
        #  to handle QList<QQmlError>...
        # https://github.com/enthought/pyside/blob/master/libpyside/signalmanager.cpp
        pass

    @QtCore.Slot(int)
    def _onQmlExit(self, code) -> None:
        # TODO test
        log.debug(f"QML exit: {code}")

    @override
    def _onQuit(self) -> None:
        # TODO https://stackoverflow.com/questions/30196113/properly-reloading-a-qqmlapplicationengine
        self._qml_engine.clearComponentCache()
        self._qml_engine.deleteLater()
        self.gcd.release()
        super()._onQuit()

    @QtCore.Slot()
    def _updateLanguage(self) -> None:
        language = Language(self._settings_manager.currentLanguageName)

        if self._language is not None:
            self._language.uninstall()
        self._language = language
        self._language.install()

        self._qml_engine.setUiLanguage(language.name)
        self._qml_engine.retranslate()

    # TODO
    @QtCore.Slot(int, str)
    def _on_network_error(self, code, error):
        self._ui_manager.online = 0 == code
        self._ui_manager.statusMessage = error
        if code:
            log.error(f"Network error: {error} code: {code}")
