from __future__ import annotations

from argparse import ArgumentParser, Namespace
from pathlib import PurePath
from typing import Callable, Optional, Type, TYPE_CHECKING, Union

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
from .coins.currency import FiatCurrencyList, FiatRate
from .coins.list import CoinList
from .config import UserConfig
from .database.db_wrapper import Database
from .key_store import KeyStore
from .language import Language
from .logger import Logger
from .network.query_manager import NetworkQueryManager
from .network.query_scheduler import NetworkQueryScheduler
from .network.services.fiat_rate import FiatRateServiceList
from .signal_handler import SignalHandler
from .utils.meta import classproperty
from .version import Product

if TYPE_CHECKING:
    from .coins.abstract.coin import AbstractCoin


class CommandLine:
    _arguments = Namespace()

    @classmethod
    def parse(cls, argv) -> None:
        # TODO sync decorations/names/description with server cli, append qsTr()
        parser = ArgumentParser(
            prog=argv[0],
            description=Product.NAME)
        parser.add_argument(
            "-l",
            "--logfile",
            help="set file name for logging")
        parser.add_argument(
            '-d',
            '--debug_mode',
            default=False,
            dest='debug_mode',
            action='store_true')
        cls._arguments = parser.parse_args(argv[1:])

    @classproperty
    def logFilePath(cls) -> Optional[PurePath]:  # noqa
        if cls._arguments.logfile:
            return PurePath(cls._arguments.logfile)
        return None

    @classproperty
    def isDebugMode(cls) -> bool:  # noqa
        return cls._arguments.debug_mode


class CoreApplication(QObject):

    _instance: CoreApplication = None

    def __init__(
            self,
            qt_class: Union[Type[QCoreApplication], Type[QApplication]],
            argv: list[str]) -> None:
        assert self.__class__._instance is None
        super().__init__()

        CoreApplication._instance = self
        self._logger = Logger.getClassLogger(__name__, self.__class__)
        self._title = "{} {}".format(Product.NAME, Product.VERSION_STRING)
        self._icon = QIcon(str(resources.ICON_FILE_PATH))
        self._language: Optional[Language] = None
        self._exit_code = 0
        self._on_exit_called = False

        self._user_config = UserConfig()
        self._user_config.load()

        self._key_store = KeyStore(self, self._user_config)

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
        # noinspection PyArgumentList
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

        self._database = Database()

        self._coin_list = []
        self._fiat_currency_list = FiatCurrencyList(self)
        self._fiat_rate_service_list = FiatRateServiceList(self)

        self._network_query_manager = NetworkQueryManager("Default")
        self._network_query_scheduler = NetworkQueryScheduler(
            self,
            self._network_query_manager)

    def _initCoinList(
            self,
            model_factory: Optional[Callable[[object], object]] = None) -> None:
        self._coin_list = CoinList(model_factory=model_factory)
        for coin in self._coin_list:
            coin.fiatRate = FiatRate(0, self._fiat_currency_list.current)

    def run(self) -> int:
        # noinspection PyTypeChecker
        QMetaObject.invokeMethod(self, "_onRunPrivate", Qt.QueuedConnection)

        assert not self._on_exit_called
        self._exit_code = self._qt_application.exec_()
        assert self._on_exit_called

        # noinspection PySimplifyBooleanCheck
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
    def isDebugMode(self) -> bool:
        return CommandLine.isDebugMode

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

    @QSlot()
    def _onRunPrivate(self) -> None:
        self._onRun()

    def _onRun(self) -> None:
        self._network_query_scheduler.start()

    def __onAboutToQuit(self) -> None:
        self._logger.debug("Shutting down...");
        # for w in QGuiApplication.topLevelWindows():
        #     w.close()
        self._onExit()

    def _onExit(self) -> None:
        assert not self._on_exit_called
        self._on_exit_called = True
        self.database.close()
        self._signal_handler.close()

