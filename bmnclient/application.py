# JOK4
from __future__ import annotations

import logging
import os
from argparse import ArgumentParser
from pathlib import PurePath
from typing import TYPE_CHECKING

from PySide2.QtCore import \
    QLocale, \
    QMetaObject, \
    QObject, \
    Qt, \
    Slot as QSlot
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication

from .coins.currency import FiatCurrencyList, FiatRate
from .coins.list import CoinList
from .config import UserConfig
from .database.db_wrapper import Database
from .key_store import KeyStore
from .logger import Logger
from .network.query_manager import NetworkQueryManager
from .network.query_scheduler import NetworkQueryScheduler
from .network.server_list import ServerList
from .network.services.fiat_rate import FiatRateServiceList
from .os_environment import PlatformPaths
from .resources import Resources
from .signal_handler import SignalHandler
from .version import Product, ProductPaths, Server

if TYPE_CHECKING:
    from typing import Callable, List, Optional, Type, Union
    from PySide2.QtCore import QCoreApplication
    from .coins.hd import HdNode
    from .language import Language


class CommandLine:
    def __init__(self, argv: List[str]) -> None:
        self._argv = argv

        parser = ArgumentParser(
            prog=self._argv[0],
            description=Product.NAME + " " + Product.VERSION_STRING)
        parser.add_argument(
            "-c",
            "--configpath",
            default=str(PlatformPaths.userApplicationConfigPath),
            type=self._expandPath,
            help="directory for configuration files; by default, it is '{}'"
            .format(str(PlatformPaths.userApplicationConfigPath)),
            metavar="PATH")
        parser.add_argument(
            "-l",
            "--logfile",
            default="stderr",
            type=self._expandPath,
            help="file that will store the log; can be one of the following "
            "special values: stdout, stderr; by default, it is 'stderr'",
            metavar="FILE")
        parser.add_argument(
            '-d',
            '--debug',
            action='store_true',
            default=False,
            help="run the application in debug mode")

        parser.add_argument(
            "-s",
            "--server-url",
            default=Server.DEFAULT_URL_LIST[0],
            type=str,
            help="alternative server URL; by default, it is '{}'"
            .format(Server.DEFAULT_URL_LIST[0]),
            metavar="URL")
        parser.add_argument(
            "--server-insecure",
            action='store_true',
            default=False,
            help="do not check the validity of server certificates")

        self._arguments = parser.parse_args(self._argv[1:])
        assert isinstance(self._arguments.configpath, PurePath)
        assert isinstance(self._arguments.logfile, PurePath)
        assert isinstance(self._arguments.debug, bool)
        assert isinstance(self._arguments.server_url, str)
        assert isinstance(self._arguments.server_insecure, bool)

    @property
    def argv(self) -> List[str]:
        return self._argv

    @property
    def configPath(self) -> PurePath:
        return self._arguments.configpath

    @property
    def logFilePath(self) -> PurePath:
        return self._arguments.logfile

    @property
    def logLevel(self) -> int:
        return logging.DEBUG if self.isDebugMode else logging.INFO

    @property
    def isDebugMode(self) -> bool:
        return self._arguments.debug

    @property
    def serverUrl(self) -> str:
        return self._arguments.server_url

    @property
    def allowServerInsecure(self) -> bool:
        return self._arguments.server_insecure

    @classmethod
    def _expandPath(cls, path: str) -> PurePath:
        return PurePath(os.path.expanduser(os.path.expandvars(path)))


class CoreApplication(QObject):
    def __init__(
            self,
            *,
            qt_class: Union[Type[QCoreApplication], Type[QApplication]],
            command_line: CommandLine,
            model_factory: Optional[Callable[[object], object]] = None) -> None:
        super().__init__()

        self._command_line = command_line
        self._logger = Logger.classLogger(self.__class__)
        self._title = "{} {}".format(Product.NAME, Product.VERSION_STRING)
        self._icon = QIcon(Resources.iconFilePath)
        self._language: Optional[Language] = None
        self._exit_code = 0
        self._on_exit_called = False
        self._run_called = False

        self._user_config = UserConfig(
            self._command_line.configPath / ProductPaths.CONFIG_FILE_NAME)
        self._user_config.load()

        self._key_store = KeyStore(
            user_config=self._user_config,
            open_callback=self._onKeyStoreOpen,
            reset_callback=self._onKeyStoreReset)

        if qt_class.instance() is not None:
            self._logger.warning("Qt Application has already been created.")
            self._qt_application = qt_class.instance()
            assert type(self._qt_application) == qt_class
        else:
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
            self._qt_application = qt_class(self._command_line.argv)

        if issubclass(qt_class, QApplication):
            qt_class.setWindowIcon(self._icon)

        # We recommend that you connect clean-up code to the aboutToQuit()
        # signal, instead of putting it in your application's main() function
        # because on some platforms the exec() call may not return.
        #
        # noinspection PyUnresolvedReferences
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

        self._database = Database(
            self,
            self._command_line.configPath / ProductPaths.DATABASE_FILE_NAME)

        self._fiat_currency_list = FiatCurrencyList(self)
        self._fiat_rate_service_list = FiatRateServiceList(self)

        self._server_list = ServerList(
            self._command_line.allowServerInsecure)
        if self._command_line.serverUrl:
            self._server_list.appendServer(self._command_line.serverUrl)
        else:
            for url in Server.DEFAULT_URL_LIST:
                self._server_list.appendServer(url)

        self._network_query_manager = NetworkQueryManager("Default")
        self._network_query_scheduler = NetworkQueryScheduler(
            self,
            self._network_query_manager)

        # initialize coins
        self._coin_list = CoinList(model_factory=model_factory)
        for coin in self._coin_list:
            coin.fiatRate = FiatRate(0, self._fiat_currency_list.current)

    def __del__(self) -> None:
        assert self._on_exit_called

    def run(self) -> int:
        # noinspection PyTypeChecker
        QMetaObject.invokeMethod(self, "_onRunPrivate", Qt.QueuedConnection)

        assert not self._on_exit_called
        self._run_called = True
        self._exit_code = self._qt_application.exec_()
        assert self._on_exit_called
        return self._exit_code

    def setExitEvent(self, code: int = 0) -> None:
        if self._run_called:
            self._qt_application.exit(code)
        elif not self._on_exit_called:
            self._exit_code = code
            self._onExit()

    @property
    def isDebugMode(self) -> bool:
        return self._command_line.isDebugMode

    @property
    def exitCode(self) -> int:
        return self._exit_code

    @property
    def userConfig(self) -> UserConfig:
        return self._user_config

    @property
    def keyStore(self) -> KeyStore:
        return self._key_store

    @property
    def database(self) -> Database:
        return self._database

    @property
    def serverList(self) -> ServerList:
        return self._server_list

    @property
    def networkQueryManager(self) -> NetworkQueryManager:
        return self._network_query_manager

    @property
    def networkQueryScheduler(self) -> NetworkQueryScheduler:
        return self._network_query_scheduler

    @property
    def coinList(self) -> CoinList:
        return self._coin_list

    @property
    def fiatCurrencyList(self) -> FiatCurrencyList:
        return self._fiat_currency_list

    @property
    def fiatRateServiceList(self) -> FiatRateServiceList:
        return self._fiat_rate_service_list

    @property
    def title(self) -> str:
        return self._title

    @property
    def icon(self) -> QIcon:
        return self._icon

    def _onKeyStoreOpen(self, root_node: HdNode) -> None:
        assert not self._database.isLoaded

        for coin in self._coin_list:
            if not coin.deriveHdNode(root_node):
                # TODO show message, force user to regenerate seed?
                pass

        self._database.open()
        self._network_query_scheduler.start(
            self._network_query_scheduler.COINS_NAMESPACE)

    def _onKeyStoreReset(self) -> None:
        self.database.remove()

    @QSlot()
    def _onRunPrivate(self) -> None:
        self._onRun()

    def _onRun(self) -> None:
        self._network_query_scheduler.start(
            self._network_query_scheduler.GLOBAL_NAMESPACE)

    def __onAboutToQuit(self) -> None:
        self._logger.debug("Shutting down...")
        # for w in QGuiApplication.topLevelWindows():
        #     w.close()
        self._onExit()

    def _onExit(self) -> None:
        assert not self._on_exit_called
        self._on_exit_called = True
        self.database.close()
        self._signal_handler.close()

        if not self._exit_code:
            self._logger.info(
                "%s terminated successfully.",
                Product.NAME)
        else:
            self._logger.warning(
                "%s terminated with error %i.",
                Product.NAME,
                self._exit_code)
