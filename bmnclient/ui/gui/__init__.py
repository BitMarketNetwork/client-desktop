from __future__ import annotations

import logging

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    QUrl, \
    Slot as QSlot
from PySide2.QtGui import QFont
from PySide2.QtQml import QQmlApplicationEngine, QQmlNetworkAccessManagerFactory
from PySide2.QtQuickControls2 import QQuickStyle
from PySide2.QtWidgets import QApplication

import bmnclient.version
from . import \
    coin_manager, \
    receive_manager, \
    settings_manager, \
    tx_controller, \
    ui_manager
from .coin_manager import CoinManager, CoinManager
from .receive_manager import ReceiveManager, ReceiveManager
from .settings_manager import SettingsManager, SettingsManager
from .ui_manager import UIManager, UIManager
from ...application import CoreApplication
from ...debug_manager import DebugManager
from ...key_store import KeyStore
from ...language import Language
from ...models.factory import modelFactory
from ...network.access_manager import NetworkAccessManager
from ...wallet.fee_manager import FeeManager

log = logging.getLogger(__name__)

QML_STYLE = "Material"
QML_FILE = "main.qml"
QML_CONTEXT_NAME = "BBackend"


class Application(CoreApplication):
    class QmlNetworkAccessManagerFactory(QQmlNetworkAccessManagerFactory):
        def create(self, parent: QObject) -> NetworkAccessManager:
            return NetworkAccessManager("QML", parent)

    def __init__(self, argv) -> None:
        super().__init__(QApplication, argv)
        self._fee_manager = FeeManager(self)
        self._initCoinList(lambda o: modelFactory(self, o))

        # TODO kill
        self._coin_manager = None
        self.networkThread.netError.connect(self._on_network_error)

        self._settings_manager = SettingsManager(self)
        self._ui_manager = UIManager(self)
        self._coin_manager = CoinManager(self)
        self._receive_manager = ReceiveManager(self)
        self._debug_manager = DebugManager(self)
        self._backend_context = BackendContext(self)

        self._settings_manager.currentLanguageNameChanged.connect(
            self._updateLanguage)

        self._initializeQml()

    def _initializeQml(self) -> None:
        QQuickStyle.setStyle(QML_STYLE)
        log.debug("QML Base URL: %s", bmnclient.resources.QML_URL)

        self._qml_network_access_manager_factory = \
            self.QmlNetworkAccessManagerFactory()
        self._qml_engine = QQmlApplicationEngine(self)

        # TODO self._engine.offlineStoragePath
        self._qml_engine.setBaseUrl(bmnclient.resources.QML_URL)
        self._qml_engine.setNetworkAccessManagerFactory(
            self._qml_network_access_manager_factory)
        # TODO replace with self._engine.warnings
        self._qml_engine.setOutputWarningsToStandardError(True)

        qml_root_context = self._qml_engine.rootContext()
        qml_root_context.setBaseUrl(bmnclient.resources.QML_URL)
        qml_root_context.setContextProperty(
            QML_CONTEXT_NAME,
            self._backend_context)

        self._qml_engine.objectCreated.connect(self._onQmlObjectCreated)
        # TODO self._qml_engine.warnings.connect(self._onQmlWarnings)
        self._qml_engine.exit.connect(self._onQmlExit)
        self._qml_engine.quit.connect(self._onQmlExit)

    @classmethod
    def instance(cls) -> Application:
        return super().instance()

    @property
    def defaultFont(self) -> QFont:
        return self._qt_application.font()

    @property
    def settingsManager(self) -> SettingsManager:
        return self._settings_manager

    @property
    def uiManager(self) -> UIManager:
        return self._ui_manager

    @property
    def coinManager(self) -> CoinManager:
        return self._coin_manager

    @property
    def receiveManager(self) -> ReceiveManager:
        return self._receive_manager

    @property
    def feeManager(self) -> FeeManager:
        return self._fee_manager

    @property
    def debugManager(self) -> DebugManager:
        return self._debug_manager

    @property
    def backendContext(self) -> BackendContext:
        return self._backend_context

    @property
    def language(self) -> Language:
        assert self._language
        return self._language

    def _onRun(self) -> None:
        super()._onRun()
        url = self._qml_engine.rootContext().resolvedUrl(QUrl(QML_FILE))
        self._updateLanguage()
        self._qml_engine.load(url)

    @QSlot(QObject, QUrl)
    def _onQmlObjectCreated(self, qml_object, url) -> None:
        if qml_object is None:
            # TODO If an error occurs, the objectCreated signal is emitted with
            #  a null pointer as parameter an
            self.setExitEvent()
        else:
            log.debug(f"QML object was created: {url.toString()}")

    @QSlot(list)
    def _onQmlWarnings(self, warning_list) -> None:
        # TODO: TypeError: Can't call meta function because I have no idea how
        #  to handle QList<QQmlError>...
        # https://github.com/enthought/pyside/blob/master/libpyside/signalmanager.cpp
        pass

    @QSlot()
    @QSlot(int)
    def _onQmlExit(self, code: int = 0) -> None:
        self.setExitEvent(code)

    def _onExit(self) -> None:
        # TODO https://stackoverflow.com/questions/30196113/properly-reloading-a-qqmlapplicationengine
        self._qml_engine.clearComponentCache()
        self._qml_engine.deleteLater()
        super()._onExit()

    @QSlot()
    def _updateLanguage(self) -> None:
        language = Language(self._settings_manager.currentLanguageName)

        if self._language is not None:
            self._language.uninstall()
        self._language = language
        self._language.install()

        self._qml_engine.setUiLanguage(language.name)
        self._qml_engine.retranslate()

    # TODO
    @QSlot(int, str)
    def _on_network_error(self, code, error):
        self._ui_manager.online = 0 == code
        self._ui_manager.statusMessage = error
        if code:
            log.error(f"Network error: {error} code: {code}")


class BackendContext(QObject):
    def __init__(self, application: Application) -> None:
        super().__init__()
        self._application = application

    @QProperty(bool, constant=True)
    def isDebugMode(self) -> bool:
        return self._application.isDebugMode

    @QProperty(DebugManager, constant=True)
    def debugManager(self) -> DebugManager:
        return self._application.debugManager

    @QProperty(KeyStore, constant=True)
    def keyStore(self) -> KeyStore:
        return self._application.keyStore

    @QProperty(SettingsManager, constant=True)
    def settingsManager(self) -> SettingsManager:
        return self._application.settingsManager

    @QProperty(UIManager, constant=True)
    def uiManager(self) -> UIManager:
        return self._application.uiManager

    @QProperty(CoinManager, constant=True)
    def coinManager(self) -> CoinManager:
        return self._application.coinManager

    @QProperty(ReceiveManager, constant=True)
    def receiveManager(self) -> ReceiveManager:
        return self._application.receiveManager
