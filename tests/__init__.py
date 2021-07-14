from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path
from random import randint
from tempfile import gettempdir
from typing import TYPE_CHECKING

from PySide2.QtWidgets import QApplication

from bmnclient.application import CommandLine, CoreApplication
from bmnclient.os_environment import Platform
from bmnclient.utils.class_property import classproperty
from bmnclient.version import Product, Timer

if TYPE_CHECKING:
    from typing import Final, Optional
    from unittest import TestCase
    MessageType = CoreApplication.MessageType


class TestApplication(CoreApplication):
    _DATA_PATH: Final = Path(__file__).parent.resolve() / "data"
    _logger_configured = False

    def __init__(
            self,
            owner: TestCase,
            *,
            config_path: Optional[Path] = None) -> None:
        command_line = ["unittest"]

        if not config_path:
            config_path = (
                    Path(gettempdir())
                    / "{:s}-{:s}.{:d}".format(
                        Product.SHORT_NAME,
                        owner.__class__.__name__,
                        randint(1, 0xffffffffffffffff))
            )
            owner.assertFalse(config_path.exists())

        command_line.append("--configpath=" + str(config_path))

        if Platform.isLinux:
            os.environ["QT_QPA_PLATFORM"] = "minimal"

        super().__init__(
            qt_class=QApplication,
            command_line=CommandLine(command_line),
            model_factory=None)

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
