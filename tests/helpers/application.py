from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path
from random import randint
from tempfile import gettempdir
from typing import TYPE_CHECKING
from unittest import TestCase

from PySide6.QtWidgets import QApplication

from bmnclient.application import CommandLine, CoreApplication
from bmnclient.debug import Debug
from bmnclient.os_environment import Platform
from bmnclient.utils.class_property import classproperty
from bmnclient.version import Product, Timer
from .coin_models import ModelsFactory

if TYPE_CHECKING:
    from typing import Final, Optional
    MessageType = CoreApplication.MessageType

Debug.setState(True)


class TestApplication(CoreApplication):
    _DATA_PATH: Final = Path(__file__).parent.parent.resolve() / "data"
    _logger_configured = False

    def __init__(
            self,
            *,
            config_path: Optional[Path] = None) -> None:
        temp_path = (
                Path(gettempdir())
                / "{:s}-tests".format(Product.SHORT_NAME.lower()))
        if not config_path:
            config_path = temp_path / "config"

        command_line = [
            "unittest",
            "--debug",
            "--config-path=" + str(config_path),
            "--temp-path=" + str(temp_path)
        ]

        if Platform.isLinux:
            os.environ["QT_QPA_PLATFORM"] = "minimal"

        super().__init__(
            qt_class=QApplication,
            command_line=CommandLine(command_line),
            model_factory=lambda o: ModelsFactory.create(self, o))

    def showMessage(
            self,
            *,
            type_: MessageType = CoreApplication.MessageType.INFORMATION,
            title: Optional[str] = None,
            text: str,
            timeout: int = Timer.UI_MESSAGE_TIMEOUT) -> None:
        pass

    @classproperty
    def dataPath(cls) -> Path:  # noqa
        return cls._DATA_PATH

    @staticmethod
    def getLogger(name: str) -> logging.Logger:
        return logging.getLogger(name)

    @classmethod
    def configureLogger(cls) -> None:
        if cls._logger_configured:
            return

        class Formatter(logging.Formatter):
            def __init__(self) -> None:
                super().__init__(
                    fmt="%(asctime)s (%(levelname)s) %(thread)016x "
                        "%(name)s[%(funcName)s:%(lineno)s]: " # noqa
                        "%(message)s",
                    datefmt=None)

            def formatTime(self, record, datefmt=None) -> str:
                return time.strftime(
                    "%Y-%m-%d %H:%M:%S.{0:03.0f} %z".format(record.msecs),
                    self.converter(record.created))

        handler = logging.StreamHandler(stream=sys.stderr)
        handler.setFormatter(Formatter())

        kwargs = {
            "level": logging.DEBUG,
            "handlers": (handler, )
        }
        logging.basicConfig(**kwargs)

        # Disable when running from Makefile
        if "MAKELEVEL" in os.environ or "TOX_ENV_NAME" in os.environ:
            logging.disable()

        cls._logger_configured = True


TestApplication.configureLogger()


class TestCaseApplication(TestCase):
    def setUp(self) -> None:
        self._application = TestApplication()
        self._key_store_password = "".join(
            str(randint(0, 9)) for _ in range(randint(6, 32)))

        self.assertTrue(self._application.keyStore.create(
            self._key_store_password))
        self.assertTrue(self._application.keyStore.open(
            self._key_store_password))

    def tearDown(self) -> None:
        self._application.setExitEvent()
