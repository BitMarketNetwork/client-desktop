from __future__ import annotations

import logging
import os
from argparse import ArgumentParser
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import (
    QLocale,
    QMetaObject,
    QObject,
    Qt,
    Slot as QSlot)
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .coins.list import CoinList
from .config import Config, ConfigKey
from .currency import FiatCurrencyList, FiatRate
from .database import Database
from .database.tables import AddressListTable, CoinListTable, TxListTable
from .debug import Debug
from .key_store import KeyStore
from .language import Language
from .logger import Logger
from .network import Network
from .network.query_manager import NetworkQueryManager
from .network.query_scheduler import NetworkQueryScheduler
from .network.server_list import ServerList
from .network.services.blockchain_explorer import BlockchainExplorerList
from .network.services.fiat_rate import FiatRateServiceList
from .os_environment import PlatformPaths
from .resources import Resources
from .signal_handler import SignalHandler
from .version import Product, ProductPaths, Server, Timer

if TYPE_CHECKING:
    from typing import List, Optional, Type, Union
    from PySide6.QtCore import QCoreApplication
    from .coins.abstract import CoinModelFactory
    from .coins.hd import HdNode


class CommandLine:
    def __init__(self, argv: List[str]) -> None:
        self._argv = argv

        parser = ArgumentParser(
            prog=os.path.basename(self._argv[0]),
            description=Product.NAME + " " + Product.VERSION_STRING)
        parser.add_argument(
            "-c",
            "--config-path",
            default=str(PlatformPaths.applicationConfigPath),
            type=self._expandPath,
            help="directory for configuration files; by default, it is '{}'"
            .format(str(PlatformPaths.applicationConfigPath)),
            metavar="PATH")
        parser.add_argument(
            "-L",
            "--local-data-path",
            default=str(PlatformPaths.applicationLocalDataPath),
            type=self._expandPath,
            help="directory for local data files; by default, it is '{}'"
            .format(str(PlatformPaths.applicationLocalDataPath)),
            metavar="PATH")
        parser.add_argument(
            "-T",
            "--temp-path",
            default=str(PlatformPaths.applicationLocalDataPath),
            type=self._expandPath,
            help="directory for temporary files; by default, it is '{}'"
            .format(str(PlatformPaths.applicationTempPath)),
            metavar="PATH")
        parser.add_argument(
            "-l",
            "--log-file",
            default="stderr",
            type=self._expandPath,
            help="file that will store the log; can be one of the following"
            " special values: stdout, stderr; by default, it is 'stderr'",
            metavar="FILE")
        parser.add_argument(
            "-d",
            "--debug",
            action="store_true",
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
            action="store_true",
            default=False,
            help="do not check the validity of server certificates")

        self._arguments = parser.parse_args(self._argv[1:])
        assert isinstance(self._arguments.config_path, Path)
        assert isinstance(self._arguments.local_data_path, Path)
        assert isinstance(self._arguments.log_file, Path)
        assert isinstance(self._arguments.debug, bool)
        assert self._arguments.debug == Debug.isEnabled
        assert isinstance(self._arguments.server_url, str)
        assert isinstance(self._arguments.server_insecure, bool)

    @property
    def argv(self) -> List[str]:
        return self._argv

    @property
    def tempPath(self) -> Path:
        return self._arguments.temp_path

    @property
    def configPath(self) -> Path:
        return self._arguments.config_path

    @property
    def localDataPath(self) -> Path:
        return self._arguments.local_data_path

    @property
    def logFilePath(self) -> Path:
        return self._arguments.log_file

    @property
    def logLevel(self) -> int:
        return logging.DEBUG if Debug.isEnabled else logging.INFO

    @property
    def serverUrl(self) -> str:
        return self._arguments.server_url

    @property
    def allowServerInsecure(self) -> bool:
        return self._arguments.server_insecure

    @classmethod
    def _expandPath(cls, path: str) -> Path:
        return Path(os.path.expanduser(os.path.expandvars(path)))


class CoreApplication(QObject):
    class MessageType(Enum):
        INFORMATION = auto()
        WARNING = auto()
        ERROR = auto()

    def __init__(
            self,
            *,
            qt_class: Union[Type[QCoreApplication], Type[QApplication]],
            command_line: CommandLine,
            model_factory: Optional[CoinModelFactory] = None) -> None:
        super().__init__()

        self._command_line = command_line
        self._logger = Logger.classLogger(self.__class__)
        self._title = "{} {}".format(Product.NAME, Product.VERSION_STRING)
        self._icon = QIcon(Resources.iconFilePath)
        self._language: Optional[Language] = None
        self._exit_code = 0
        self._on_exit_called = False
        self._run_called = False

        self._config = Config(
            self._command_line.configPath
            / ProductPaths.CONFIG_FILE_NAME)
        self._config.load()

        self._key_store = KeyStore(
            self,
            open_callback=self._onKeyStoreOpen,
            reset_callback=self._onKeyStoreReset)

        if qt_class.instance() is not None:
            self._logger.warning("Qt Application has already been created.")
            self._qt_application = qt_class.instance()
            assert type(self._qt_application) == qt_class
        else:
            # Prepare QCoreApplication
            QLocale.setDefault(QLocale.c())

            qt_class.setAttribute(Qt.AA_DisableShaderDiskCache)

            qt_class.setApplicationName(Product.NAME)
            qt_class.setApplicationVersion(Product.VERSION_STRING)
            qt_class.setOrganizationName(Product.MAINTAINER)
            qt_class.setOrganizationDomain(Product.MAINTAINER_DOMAIN)

            # QCoreApplication
            self._qt_application = qt_class([
                self._command_line.argv[0],
            ])

        if issubclass(qt_class, QApplication):
            qt_class.setWindowIcon(self._icon)
            qt_class.setDesktopFileName(Product.SHORT_NAME + ".desktop")

        # We recommend that you connect clean-up code to the aboutToQuit()
        # signal, instead of putting it in your application's main() function
        # because on some platforms the exec() call may not return.
        #
        # noinspection PyUnresolvedReferences
        self._qt_application.aboutToQuit.connect(
            self.__onAboutToQuit,
            Qt.DirectConnection)

        # SignalHandler
        self._signal_handler = SignalHandler()
        self._signal_handler.sigintSignal.connect(
            self.setExitEvent,
            Qt.QueuedConnection)
        self._signal_handler.sigquitSignal.connect(
            self.setExitEvent,
            Qt.QueuedConnection)
        self._signal_handler.sigtermSignal.connect(
            self.setExitEvent,
            Qt.QueuedConnection)

        self._init_database()
        self._init_network()
        self._init_coins(model_factory)

    def _init_database(self) -> None:
        self._database = Database(
            self,
            self._command_line.configPath / ProductPaths.DATABASE_FILE_NAME)

    def _init_network(self) -> None:
        Network.configure()

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

    def _init_coins(
            self,
            model_factory: Optional[CoinModelFactory] = None) -> None:
        self._fiat_currency_list = FiatCurrencyList(self)
        self._fiat_rate_service_list = FiatRateServiceList(self)
        self._blockchain_explorer_list = BlockchainExplorerList(self)

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
        self._exit_code = self._qt_application.exec()
        assert self._on_exit_called

        if not self._exit_code:
            self._logger.info(
                "%s terminated successfully.",
                Product.NAME)
        else:
            self._logger.warning(
                "%s terminated with error %i.",
                Product.NAME,
                self._exit_code)
        return self._exit_code

    def setExitEvent(self, code: int = 0) -> None:
        if self._run_called:
            self._qt_application.exit(code)
        elif not self._on_exit_called:
            self._exit_code = code
            self._onExit()

    @property
    def tempPath(self) -> Path:
        return self._command_line.tempPath

    @property
    def configPath(self) -> Path:
        return self._command_line.configPath

    @property
    def config(self) -> Config:
        return self._config

    @property
    def exitCode(self) -> int:
        return self._exit_code

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
    def blockchainExplorerList(self) -> BlockchainExplorerList:
        return self._blockchain_explorer_list

    @property
    def title(self) -> str:
        return self._title

    @property
    def icon(self) -> QIcon:
        return self._icon

    @property
    def language(self) -> Optional[Language]:
        return self._language

    def updateTranslation(self) -> None:
        language_name = self._config.get(ConfigKey.UI_LANGUAGE, str)
        if not language_name:
            language_name = Language.primaryName
        language = Language(language_name)

        if self._language is not None:
            self._logger.info(
                "Removing translation '%s'.",
                self._language.name)
            self._language.uninstall()

        self._language = language
        self._logger.info(
            "Setting translation '%s'.",
            self._language.name)
        self._language.install()

    def showMessage(
            self,
            *,
            type_: MessageType = MessageType.INFORMATION,
            title: Optional[str] = None,
            text: str,
            timeout: int = Timer.UI_MESSAGE_TIMEOUT) -> None:
        raise NotImplementedError

    def _onKeyStoreOpen(self, root_node: Optional[HdNode]) -> None:
        if root_node is None:
            return
        assert not self._database.isOpen

        for coin in self._coin_list:
            if not coin.deriveHdNode(root_node):
                # TODO show message, force user to regenerate seed?
                pass

        if self._database.open():
            if not self._loadWalletData():
                self._database.close()
        if not self._database.isOpen:
            # TODO show message, allow continue without database
            pass

        self._network_query_scheduler.start(
            self._network_query_scheduler.GLOBAL_NAMESPACE)
        self._network_query_scheduler.start(
            self._network_query_scheduler.COINS_NAMESPACE)

    def _onKeyStoreReset(self) -> None:
        if not self._database.remove():
            # TODO show message if failed
            pass

    def _loadWalletData(self) -> bool:  # TODO move to coins
        try:
            with self._database.transaction() as cursor:
                for coin in self._coin_list:
                    if not self._database[CoinListTable].deserialize(
                            cursor,
                            coin):
                        self._logger.debug(
                            "Cannot deserialize coin '%s' from database.",
                            coin.name)
                        self._database[CoinListTable].serialize(cursor, coin)
                        continue

                    self._database[AddressListTable].deserializeAll(
                            cursor,
                            coin)

                    for address in coin.addressList:
                        self._database[TxListTable].deserializeAll(
                            cursor,
                            address)
        except (Database.engine.Error, Database.engine.Warning) as e:
            self._logger.error(
                "Failed to read wallet from database: %s",
                str(e))
            return False
        return True

    @QSlot()
    def _onRunPrivate(self) -> None:
        self._onRun()

    def _onRun(self) -> None:
        self.updateTranslation()

    def __onAboutToQuit(self) -> None:
        self._logger.debug("Shutting down...")
        # if isinstance(self._qt_application, QApplication):
        #     for w in self._qt_application.topLevelWindows():
        #         w.close()
        self._onExit()

    def _onExit(self) -> None:
        assert not self._on_exit_called
        self._on_exit_called = True
        self._database.close()
        self._signal_handler.close()
