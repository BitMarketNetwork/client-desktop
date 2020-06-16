import  sys
import  traceback
import  logging
import  pathlib
from    PySide2 import QtCore as qt_core
from    ..config import logger as   e_config_logger
from    ..config import local as    e_config



def create_handler(file_name : str) -> logging.Handler:
    if isinstance(file_name,(str,pathlib.Path)):
        handler = logging.FileHandler(file_name, 'w', encoding='utf-8')
    else:
        handler = logging.StreamHandler()
    return handler

def create_qt_logger():
    logger = logging.getLogger('qt')
    handler = logging.StreamHandler()
    handler.setLevel(e_config_logger.DEFAULT_LEVEL)
    logger.addHandler(handler)
    logger.propagate = False
    return logger

__qt_logger = create_qt_logger()

def qt_message_handler(mode, context, mess: str) -> None:
    if context.file or context.function:
        file = context.file or 'none'
        mess = f"{file.rpartition('/')[2].rstrip()} - {context.line} [{context.function}]: {mess} "
    if mode == qt_core.QtInfoMsg:
        __qt_logger.info(mess)
    elif mode == qt_core.QtWarningMsg:
        __qt_logger.warn(mess)
    elif mode == qt_core.QtCriticalMsg:
        __qt_logger.critical(mess)
    elif mode == qt_core.QtFatalMsg:
        __qt_logger.fatal(mess)
    else:
        __qt_logger.debug(mess)


class DispatchingFormatter:

    def __init__(self, formatters, default_formatter):
        self._formatters = formatters
        self._default_formatter = default_formatter

    def format(self, record):
        formatter = self._formatters.get(record.name, self._default_formatter)
        return formatter.format(record)




def turn_logger( on ):
    if on:
        handler = create_handler(e_config.log_file())
        handler.setFormatter(DispatchingFormatter({
            'qt': logging.Formatter('qml:(%(levelname)s) %(message)s'), },
            logging.Formatter( '### (%(levelname)s) <[%(threadName)s>  %(filename)s - %(lineno)s [%(funcName)s]: %(message)s'),
        ))
        logging.basicConfig(
            style='%',
            level=e_config_logger.DEFAULT_LEVEL,
            handlers=(handler,)
            )
        # coloredlogs.install(
        #     level = e_config_logger.DEFAULT_LEVEL,
        #     fmt = '### %(asctime)s <[%(threadName)s> [%(filename)s:%(lineno)s %(funcName)s]: %(message)s',
        #     datefmt = '%M:%S',
        #     reconfigure = True,
        # )
        # coloredlogs.install(
        #     level = e_config_logger.DEFAULT_LEVEL,
        #     fmt = 'QML %(message)s',
        #     datefmt = '%M:%S',
        #     reconfigure = True,
        #     logger = __qt_logger,
        #     level_styles = {
        #         'debug': {'color': 'cyan'},
        #         'warning': {'color': 'magenta'},
        #         'error': {'color': 'red'},
        #     },
        # )
        qt_core.qInstallMessageHandler(qt_message_handler)
    else:
        qt_core.qInstallMessageHandler(None)


def fatal_exception():
    message = (
        "FATAL RUNTIME EXCEPTION:\n"
        + traceback.format_exc(limit=5, chain=True))
    logging.getLogger().critical(message)
    sys.exit(1)

def create():
    pass