# JOK++
from __future__ import annotations

import logging
import os
import sys
import time
import traceback
from pathlib import PurePath
from threading import Lock
from typing import Optional, TYPE_CHECKING, Type

from PySide2 import QtCore

from .platform import Platform
from .version import Product

if TYPE_CHECKING:
    from json import JSONDecodeError


_qt_logger: Optional[logging.Logger] = None
_configure_lock = Lock()
_is_configured = False


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


class FileHandler(logging.FileHandler):
    pass


class StreamHandler(logging.StreamHandler):
    pass


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


class Logger:
    @classmethod
    def configure(
            cls,
            file_path: Optional[PurePath] = None,
            level: int = logging.DEBUG) -> None:
        global _is_configured
        global _configure_lock
        global _qt_logger

        with _configure_lock:
            if _is_configured:
                return

            if file_path:
                handler = FileHandler(
                    str(file_path),
                    mode="at",
                    encoding=Product.ENCODING)
            else:
                handler = StreamHandler(stream=sys.stderr)
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
            if Platform.TYPE not in (
                    Platform.Type.DARWIN,
                    Platform.Type.WINDOWS):
                QtCore.qInstallMessageHandler(_qtMessageHandler)

            _is_configured = True

    @classmethod
    def fatalException(cls, logger: Optional[Logger] = None) -> None:
        cls.configure()
        message = (
                "FATAL EXCEPTION:\n"
                + traceback.format_exc(limit=5, chain=True))
        if not logger:
            logger = logging.getLogger()
        logger.critical("%s", message)
        os.abort()

    @classmethod
    def fatal(cls, message: str, logger: Optional[Logger] = None) -> None:
        cls.configure()
        if not logger:
            logger = logging.getLogger()
        logger.critical("FATAL ERROR: %s", message)
        os.abort()

    @classmethod
    def errorToString(cls, error: int, message: str) -> str:
        return "Error {:d}: {:s}".format(error, message)

    @classmethod
    def osErrorToString(cls, e: OSError) -> str:
        return cls.errorToString(e.errno, e.strerror)

    @classmethod
    def exceptionToString(cls, e: Exception):
        return "Error: " + str(e)

    @classmethod
    def jsonDecodeErrorToString(cls, e: JSONDecodeError) -> str:
        return \
            "JSON error at offset {:d}:{:d}: {:s}"\
            .format(e.lineno, e.pos, e.msg)

    @classmethod
    def nameSuffix(cls, suffix: Optional[str]) -> str:
        if suffix:
            return "[" + suffix + "]"
        else:
            return ""

    @classmethod
    def getClassLogger(
            cls,
            module_name: str,
            owner_cls: Type,
            suffix: Optional[str] = None) -> logging.Logger:
        name = \
            ".".join((module_name, owner_cls.__name__)) \
            + cls.nameSuffix(suffix)
        return logging.getLogger(name)
