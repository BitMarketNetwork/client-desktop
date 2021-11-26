from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from threading import Lock
from time import strftime
from typing import TYPE_CHECKING

from PySide6.QtCore import qInstallMessageHandler, QtMsgType

from .os_environment import Platform
from .utils.string import StringUtils
from .version import Product

if TYPE_CHECKING:
    from json import JSONDecodeError
    from typing import Optional, Type
    from PySide6.QtCore import QMessageLogContext
    from .utils.string import ClassStringKeyTuple


_qt_logger: Optional[logging.Logger] = None
_configure_lock = Lock()
_is_configured = False


def _qtMessageHandler(
        message_type: QtMsgType,
        _: QMessageLogContext,
        message: str) -> None:
    global _qt_logger
    if message_type == QtMsgType.QtDebugMsg:
        _qt_logger.debug(message)
    elif message_type == QtMsgType.QtInfoMsg:
        _qt_logger.info(message)
    elif message_type == QtMsgType.QtWarningMsg:
        _qt_logger.warning(message)
    elif message_type == QtMsgType.QtCriticalMsg:
        _qt_logger.critical(message)
    elif message_type == QtMsgType.QtFatalMsg:
        _qt_logger.critical(message)
        os.abort()
    elif message_type == QtMsgType.QtSystemMsg:
        _qt_logger.critical(message)
    else:
        _qt_logger.error(message)


class _FileHandler(logging.FileHandler):
    pass


class _StreamHandler(logging.StreamHandler):
    pass


class _Formatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s (%(levelname)s) %(thread)016x %(name)s: "
                "%(message)s",
            datefmt=None)

    def formatTime(self, record, datefmt=None) -> str:
        return strftime(
            "%Y-%m-%d %H:%M:%S.{0:03.0f} %z".format(record.msecs),
            self.converter(record.created))


class Logger:
    @classmethod
    def configure(
            cls,
            file_path: Path = Path("stderr"),
            level: int = logging.DEBUG) -> None:
        global _is_configured
        global _configure_lock
        global _qt_logger

        with _configure_lock:
            if _is_configured:
                return

            if str(file_path) == "stderr":
                handler = _StreamHandler(stream=sys.stderr)
            elif str(file_path) == "stdout":
                handler = _StreamHandler(stream=sys.stdout)
            else:
                handler = _FileHandler(
                    str(file_path),
                    mode="at",
                    encoding=Product.ENCODING)
            handler.setFormatter(_Formatter())

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
            _qt_logger = logging.getLogger("Qt")
            qInstallMessageHandler(_qtMessageHandler)

            _is_configured = True

    @classmethod
    def fatalException(cls, logger: Optional[Logger] = None) -> None:
        cls.configure()
        from traceback import format_exc
        if not logger:
            logger = logging.getLogger()
        logger.critical(
            "FATAL EXCEPTION:\n%s",
            format_exc(limit=-5, chain=True))
        os.abort()

    @classmethod
    def fatal(cls, message: str, logger: Optional[Logger] = None) -> None:
        cls.configure()
        if not logger:
            logger = logging.getLogger()
        logger.critical("FATAL ERROR: %s", message)
        os.abort()

    @classmethod
    def errorString(cls, error: int, message: str) -> str:
        return "Error {:d}: {:s}".format(error, message)

    @classmethod
    def osErrorString(cls, e: OSError) -> str:
        return cls.errorString(e.errno, e.strerror)

    @classmethod
    def exceptionString(cls, e: Exception):
        return "Error: " + str(e)

    @classmethod
    def jsonDecodeErrorString(cls, e: JSONDecodeError) -> str:
        return \
            "JSON error at offset {:d}:{:d}: {:s}" \
            .format(e.lineno, e.pos, e.msg)

    @classmethod
    def classLogger(
            cls,
            cls_: Type,
            *key_list: ClassStringKeyTuple) \
            -> logging.Logger:
        return logging.getLogger(StringUtils.classString(cls_, *key_list))
