# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    QUrl, \
    Slot as QSlot
from PySide2.QtQml import QQmlApplicationEngine, QQmlNetworkAccessManagerFactory
from PySide2.QtQuickControls2 import QQuickStyle
from PySide2.QtWidgets import QApplication

from .debug_manager import DebugManager
from .models.coin import CoinListModel
from .models.factory import ModelsFactory
from .models.settings import SettingsModel
from .ui_manager import UIManager
from ...application import CoreApplication
from ...language import Language
from ...network.access_manager import NetworkAccessManager
from ...resources import Resources
from ...version import Gui

if TYPE_CHECKING:
    from typing import List
    from PySide2.QtGui import QFont
    from PySide2.QtQml import QQmlError
    from ...application import CommandLine
    from ...key_store import KeyStore


class GuiApplication(CoreApplication):
    class QmlNetworkAccessManagerFactory(QQmlNetworkAccessManagerFactory):
        def create(self, parent: QObject) -> NetworkAccessManager:
            return NetworkAccessManager("QML", parent)

    def __init__(self, command_line: CommandLine) -> None:
        super().__init__(
            qt_class=QApplication,
            command_line=command_line,
            model_factory=lambda o: ModelsFactory.create(self, o))

        self._ui_manager = UIManager(self)
        self._debug_manager = DebugManager(self)
        self._backend_context = BackendContext(self)

        self._initializeQml()

    def _initializeQml(self) -> None:
        QQuickStyle.setStyle(Gui.QML_STYLE)
        self._logger.debug("QML Base URL: %s", Resources.qmlUrl.toString())

        self._qml_network_access_manager_factory = \
            self.QmlNetworkAccessManagerFactory()
        self._qml_engine = QQmlApplicationEngine(self)

        # TODO self._engine.offlineStoragePath
        self._qml_engine.setBaseUrl(Resources.qmlUrl)
        self._qml_engine.setNetworkAccessManagerFactory(
            self._qml_network_access_manager_factory)
        # TODO replace with self._engine.warnings
        self._qml_engine.setOutputWarningsToStandardError(True)

        qml_root_context = self._qml_engine.rootContext()
        qml_root_context.setBaseUrl(Resources.qmlUrl)
        qml_root_context.setContextProperty(
            Gui.QML_CONTEXT_NAME,
            self._backend_context)

        self._qml_engine.objectCreated.connect(self._onQmlObjectCreated)
        # TODO self._qml_engine.warnings.connect(self._onQmlWarnings)
        self._qml_engine.exit.connect(self._onQmlExit)
        self._qml_engine.quit.connect(self._onQmlExit)

    @property
    def defaultFont(self) -> QFont:
        return self._qt_application.font()

    @property
    def uiManager(self) -> UIManager:
        return self._ui_manager

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
        url = self._qml_engine.rootContext().resolvedUrl(QUrl(Gui.QML_FILE))
        self.updateTranslation()
        self._qml_engine.load(url)

    @QSlot(QObject, QUrl)
    def _onQmlObjectCreated(self, qml_object: QObject, url: QUrl) -> None:
        if qml_object is None:
            # TODO If an error occurs, the objectCreated signal is emitted with
            #  a null pointer as parameter an.
            self.setExitEvent()
        else:
            self._logger.debug("QML object was created: %s", url.toString())

    @QSlot(list)
    def _onQmlWarnings(self, warning_list: List[QQmlError]) -> None:
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

    def updateTranslation(self) -> None:
        language = Language(self._backend_context.settings.language.currentName)

        if self._language is not None:
            self._logger.info(
                "Removing the UI translation '%s'.",
                self._language.name)
            self._language.uninstall()

        self._language = language
        self._logger.info(
            "Setting UI translation '%s'.",
            self._language.name)
        self._language.install()

        self._qml_engine.setUiLanguage(language.name)
        self._qml_engine.retranslate()


class BackendContext(QObject):
    def __init__(self, application: GuiApplication) -> None:
        super().__init__()
        self._application = application

        self._coin_list_model = CoinListModel(
            self._application,
            self._application.coinList)
        self._settings_model = SettingsModel(self._application)

    @QProperty(bool, constant=True)
    def isDebugMode(self) -> bool:
        return self._application.isDebugMode

    @QProperty(QObject, constant=True)
    def debugManager(self) -> DebugManager:
        return self._application.debugManager

    @QProperty(QObject, constant=True)
    def keyStore(self) -> KeyStore:
        return self._application.keyStore

    @QProperty(QObject, constant=True)
    def settings(self) -> SettingsModel:
        return self._settings_model

    @QProperty(QObject, constant=True)
    def uiManager(self) -> UIManager:
        return self._application.uiManager

    @QProperty(QObject, constant=True)
    def coinList(self) -> CoinListModel:
        return self._coin_list_model
