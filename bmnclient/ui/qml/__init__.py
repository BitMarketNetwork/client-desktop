from __future__ import annotations

from typing import TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    QUrl, \
    Slot as QSlot
from PySide2.QtQml import \
    QQmlApplicationEngine, \
    QQmlNetworkAccessManagerFactory
from PySide2.QtQuick import QQuickWindow
from PySide2.QtQuickControls2 import QQuickStyle

from .dialogs import DialogManager
from .dialogs.basic import AlphaDialog, QuitDialog
from .models.clipboard import ClipboardModel
from .models.coin import CoinListModel
from .models.debug import DebugModel
from .models.factory import ModelsFactory
from .models.key_store import KeyStoreModel
from .models.password import PasswordModel
from .models.settings import SettingsModel
from ..gui import GuiApplication
from ...network.access_manager import NetworkAccessManager
from ...resources import Resources
from ...version import Gui, ProductPaths
from ...os_environment import PlatformPaths
import os

if TYPE_CHECKING:
    from typing import Iterable, List
    from PySide2.QtQml import QQmlError
    from .dialogs import AbstractDialog
    from ...application import CommandLine


class QmlApplication(GuiApplication):
    class QmlNetworkAccessManagerFactory(QQmlNetworkAccessManagerFactory):
        def create(self, parent: QObject) -> NetworkAccessManager:
            return NetworkAccessManager("QML", parent)

    def __init__(self, *, command_line: CommandLine) -> None:
        super().__init__(
            command_line=command_line,
            model_factory=lambda o: ModelsFactory.create(self, o))
        self._qml_context = QmlContext(self)

        QQuickStyle.setStyle(Gui.QML_STYLE)
        self._logger.debug("QML Base URL: %s", Resources.qmlUrl.toString())

        self._qml_network_access_manager_factory = \
            self.QmlNetworkAccessManagerFactory()
        self._qml_engine = QQmlApplicationEngine()

        os.environ['QML_DISK_CACHE_PATH'] = \
            str(PlatformPaths.applicationLocalDataPath / ProductPaths.QML_CACHE_PATH)
        self._qml_engine.setOfflineStoragePath(
            str(PlatformPaths.applicationLocalDataPath / ProductPaths.QML_OFFLINE_STORAGE_PATH))
        self._qml_engine.setBaseUrl(Resources.qmlUrl)
        self._qml_engine.setNetworkAccessManagerFactory(
            self._qml_network_access_manager_factory)
        # TODO replace with self._engine.warnings
        self._qml_engine.setOutputWarningsToStandardError(True)

        context = self._qml_engine.rootContext()
        context.setBaseUrl(Resources.qmlUrl)
        context.setContextProperty(Gui.QML_CONTEXT_NAME, self._qml_context)

        self._qml_engine.objectCreated.connect(self._onQmlObjectCreated)
        # TODO self._qml_engine.warnings.connect(self._onQmlWarnings)
        self._qml_engine.exit.connect(self._onQmlExit)
        self._qml_engine.quit.connect(self._onQmlExit)

    @property
    def qmlContext(self) -> QmlContext:
        return self._qml_context

    @property
    def topLevelWindowList(self) -> Iterable[QQuickWindow]:
        return list(filter(
            lambda w: isinstance(w, QQuickWindow),
            super().topLevelWindowList))

    def updateTranslation(self) -> None:
        super().updateTranslation()
        self._qml_engine.setUiLanguage(self._language.name)
        self._qml_engine.retranslate()

    def _onRun(self) -> None:
        super()._onRun()
        url = QUrl(Gui.QML_FILE)
        url = self._qml_engine.rootContext().resolvedUrl(url)
        self._qml_engine.load(url)

    def _onExit(self) -> None:
        # TODO
        # https://stackoverflow.com/questions/30196113/properly-reloading-a-qqmlapplicationengine
        self._qml_engine.clearComponentCache()
        self._qml_engine.deleteLater()
        super()._onExit()

    def _onQmlObjectCreated(self, qml_object: QObject, url: QUrl) -> None:
        if qml_object is None:
            # TODO If an error occurs, the objectCreated signal is emitted with
            #  a null pointer as parameter an.
            self.setExitEvent(1)
        else:
            self._logger.debug("QML object was created: %s", url.toString())

    def _onQmlWarnings(self, warning_list: List[QQmlError]) -> None:
        # TODO: TypeError: Can't call meta function because I have no idea how
        #  to handle QList<QQmlError>...
        # https://github.com/enthought/pyside/blob/master/libpyside/signalmanager.cpp
        pass

    def _onQmlExit(self, code: int = 0) -> None:
        self.setExitEvent(code)


class QmlContext(QObject):
    def __init__(self, application: QmlApplication) -> None:
        super().__init__()
        self._application = application

        self._coin_list_model = CoinListModel(
            self._application,
            self._application.coinList)
        self._clipboard_model = ClipboardModel(self._application)
        self._key_store_model = KeyStoreModel(self._application)
        self._settings_model = SettingsModel(self._application)
        self._dialog_manager = DialogManager(self)
        self._debug_model = DebugModel(self._application)
        self._password_model = PasswordModel()

    @QSlot()
    def onCompleted(self) -> None:
        AlphaDialog(self._dialog_manager).open()
        self._application.show()

    # noinspection PyTypeChecker
    @QSlot(result=bool)
    def onClosing(self) -> bool:
        if self._settings_model.systemTray.closeToTray:
            self._application.show(False)
        else:
            self.onQuitRequest()
        return False

    @QSlot()
    def onQuitRequest(self) -> None:
        self._application.show(True)
        QuitDialog(self._dialog_manager).open()

    @QSlot(int)
    def exit(self, code: int) -> None:
        self._application.setExitEvent(code)

    @QProperty(str, constant=True)
    def title(self) -> str:
        return self._application.title

    @QProperty(QObject, constant=True)
    def coinList(self) -> CoinListModel:
        return self._coin_list_model

    @QProperty(QObject, constant=True)
    def clipboard(self) -> ClipboardModel:
        return self._clipboard_model

    @QProperty(QObject, constant=True)
    def keyStore(self) -> KeyStoreModel:
        return self._key_store_model

    @QProperty(QObject, constant=True)
    def settings(self) -> SettingsModel:
        return self._settings_model

    @QProperty(QObject, constant=True)
    def dialogManager(self) -> DialogManager:
        return self._dialog_manager

    @QProperty(QObject, constant=True)
    def debug(self) -> DebugModel:
        return self._debug_model

    @QProperty(QObject, constant=True)
    def password(self) -> PasswordModel:
        return self._password_model
