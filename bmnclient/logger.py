# JOK+
import logging
import os
import sys
import time
import traceback
from threading import Lock
from typing import Optional, Type

from PySide2 import QtCore

from .platform import CURRENT_PLATFORM, Platform
from .version import Product

_qt_logger: Optional[logging.Logger] = None
_configure_lock = Lock()
_is_configured = False


class Formatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__(
            fmt='%(asctime)s (%(levelname)s) %(name)s-%(threadName)s: '
                '%(message)s',
            datefmt=None)

    def formatTime(self, record, datefmt=None) -> str:
        return time.strftime(
            "%Y-%m-%d %H:%M:%S.{0:03.0f} %z".format(record.msecs),
            self.converter(record.created))


def _qtMessageHandler(message_type, context, message) -> None:
    global _qt_logger
    if message_type == QtCore.QtMsgType.QtDebugMsg:
        _qt_logger.debug(message)
    elif message_type == QtCore.QtMsgType.QtInfoMsg:
        _qt_logger.info(message)
    elif message_type == QtCore.QtMsgType.QtWarningMsg:
        _qt_logger.warning(message)
    elif message_type == QtCore.QtMsgType.QtCriticalMsg:
        _qt_logger.critical(message)
    elif message_type == QtCore.QtMsgType.QtFatalMsg:
        _qt_logger.critical(message)
        os.abort()
    elif message_type == QtCore.QtMsgType.QtSystemMsg:
        _qt_logger.critical(message)
    else:
        _qt_logger.error(message)


def configure(file_path: str = None, level: int = logging.DEBUG) -> None:
    global _is_configured
    global _configure_lock
    global _qt_logger

    with _configure_lock:
        if _is_configured:
            return

        # TODO pathlib
        if isinstance(file_path, str) and len(file_path) > 0:
            handler = logging.FileHandler(
                file_path,
                mode="at",
                encoding=Product.ENCODING)
        else:
            handler = logging.StreamHandler(stream=sys.stderr)
        handler.setFormatter(Formatter())

        logging.addLevelName(logging.DEBUG, "dd")
        logging.addLevelName(logging.INFO, "ii")
        logging.addLevelName(logging.WARNING, "WW")
        logging.addLevelName(logging.ERROR, "EE")
        logging.addLevelName(logging.CRITICAL, "CC")

        kwargs = {
            "level": level,
            "handlers": (handler,)
        }
        logging.basicConfig(**kwargs)
        _qt_logger = logging.getLogger("qt")

        # TODO I found this deadlock only on macOS (10.14 - 11.0), I have to
        #  disable the custom handler for this OS...
        #  pyside-setup/sources/pyside2/PySide2/glue/qtcore.cpp:
        #  msgHandlerCallback()
        #  -> Shiboken::GilState::GilState()
        #  -> PyGILState_Ensure()
        #  == deadlock
        # 2021.01.22: Now i found this deadlock on Windows...
        if CURRENT_PLATFORM not in (Platform.DARWIN, Platform.WINDOWS):
            QtCore.qInstallMessageHandler(_qtMessageHandler)

        _is_configured = True


def fatalException() -> None:
    configure()
    message = (
            "FATAL EXCEPTION:\n"
            + traceback.format_exc(limit=5, chain=True))
    logging.getLogger().critical(message)
    os.abort()


def fatal(message: str) -> None:
    configure()
    logging.getLogger().critical("FATAL ERROR: " + message)
    os.abort()


def osErrorToString(e: OSError) -> str:
    return "Error {:d}: {:s}".format(e.errno, e.strerror)


def getClassLogger(
        module_name: str,
        cls: Type,
        suffix: Optional[str] = None) -> logging.Logger:
    name = ".".join((module_name, cls.__name__))
    if suffix is not None:
        name += "[" + suffix + "]"
    return logging.getLogger(name)
