from __future__ import annotations

from functools import partial
from typing import Union, Optional, Type

from PySide2.QtCore import \
    QCoreApplication, \
    QLocale, \
    QMetaObject, \
    QObject, \
    Qt, \
    Slot as QSlot
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication

from . import resources
from .coins.list import CoinList
from .config import UserConfig
from .key_store import KeyStore
from .language import Language
from .logger import getClassLogger
from .server.thread import ServerThread
from .signal_handler import SignalHandler
from .version import Product
from .wallet.thread import WalletThread


class CoreApplication(QObject):
    _instance: CoreApplication = None

    def __init__(
            self,
            qt_class: Union[Type[QCoreApplication], Type[QApplication]],
            argv: list[str]) -> None:
        assert self.__class__._instance is None
        super().__init__()

        CoreApplication._instance = self
        self._logger = getClassLogger(__name__, self.__class__)
        self._title = "{} {}".format(Product.NAME, Product.VERSION_STRING)
        self._icon = QIcon(str(resources.ICON_FILE_PATH))
        self._language: Optional[Language] = None
        self._exit_code = 0
        self._on_exit_called = False

        self._user_config = UserConfig()
        self._user_config.load()

        self._key_store = KeyStore(self._user_config)

        # Prepare QCoreApplication
        QLocale.setDefault(QLocale.c())

        qt_class.setAttribute(Qt.AA_EnableHighDpiScaling)
        qt_class.setAttribute(Qt.AA_UseHighDpiPixmaps)
        qt_class.setAttribute(Qt.AA_DisableShaderDiskCache)
        qt_class.setAttribute(Qt.AA_DisableWindowContextHelpButton)

        qt_class.setApplicationName(Product.NAME)
        qt_class.setApplicationVersion(Product.VERSION_STRING)
        qt_class.setOrganizationName(Product.MAINTAINER)
        qt_class.setOrganizationDomain(Product.MAINTAINER_DOMAIN)

        # QCoreApplication
        self._qt_application = qt_class(argv)

        if issubclass(qt_class, QApplication):
            qt_class.setWindowIcon(self._icon)

        # We recommend that you connect clean-up code to the aboutToQuit()
        # signal, instead of putting it in your application's main() function
        # because on some platforms the exec() call may not return.
        self._qt_application.aboutToQuit.connect(
            self.__onAboutToQuit,
            Qt.DirectConnection)

        # SignalHandler
        self._signal_handler = SignalHandler(self)
        self._signal_handler.SIGINT.connect(
            self.setExitEvent,
            Qt.QueuedConnection)
        self._signal_handler.SIGQUIT.connect(
            self.setExitEvent,
            Qt.QueuedConnection)
        self._signal_handler.SIGTERM.connect(
            self.setExitEvent,
            Qt.QueuedConnection)

        self._wallet_thread = WalletThread()
        self._server_thread = ServerThread()

        self._coin_list = CoinList()

        # TODO
        for coin in self._coin_list:
            self._server_thread.heightChanged.connect(
                partial(
                    lambda c: self._server_thread.retrieveCoinHistory.emit(c),
                    coin),
                Qt.UniqueConnection)
            self._server_thread.heightChanged.connect(
                partial(
                    lambda c: self._wallet_thread.heightChanged.emit(c),
                    coin),
                Qt.UniqueConnection)

    def run(self) -> int:
        QMetaObject.invokeMethod(self, "_onRunPrivate", Qt.QueuedConnection)

        assert not self._on_exit_called
        self._exit_code = self._qt_application.exec_()
        assert self._on_exit_called

        if self._exit_code == 0:
            self._logger.info(
                "%s terminated successfully.",
                Product.NAME)
        else:
            self._logger.warning(
                "%s terminated with error.",
                Product.NAME)
        return self._exit_code

    def setExitEvent(self, code: int = 0) -> None:
        self._qt_application.exit(code)

    @classmethod
    def instance(cls) -> CoreApplication:
        return cls._instance

    @property
    def exitCode(self) -> int:
        return self._exit_code

    @property
    def userConfig(self) -> UserConfig:
        return self._user_config

    @property
    def keyStore(self) -> KeyStore:
        return self._key_store

    # TODO
    @property
    def databaseThread(self) -> WalletThread:
        return self._wallet_thread

    # TODO
    @property
    def networkThread(self) -> ServerThread:
        return self._server_thread

    @property
    def coinList(self) -> CoinList:
        return self._coin_list

    @property
    def title(self) -> str:
        return self._title

    @property
    def icon(self) -> QIcon:
        return self._icon

    @QSlot()
    def _onRunPrivate(self) -> None:
        self._onRun()

    def _onRun(self) -> None:
        self._wallet_thread.start()
        self._server_thread.start()

    def __onAboutToQuit(self) -> None:
        self._logger.debug("Shutting down...");
        # for w in QGuiApplication.topLevelWindows():
        #     w.close()
        self._onExit()

    def _onExit(self) -> None:
        assert not self._on_exit_called

        # TODO
        QMetaObject.invokeMethod(
            self._server_thread.network,
            "abort",
            Qt.QueuedConnection)
        QMetaObject.invokeMethod(
            self._wallet_thread.database,
            "abort",
            Qt.QueuedConnection)
        for thread in (self._server_thread, self._wallet_thread):
            # TODO logger
            thread.exit()
            thread.wait()

        self._on_exit_called = True
        self._signal_handler.close()
