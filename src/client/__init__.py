import sys
import logging

import PySide2.QtCore    as qt_core

from .config import local as e_config_local
from .config import version as e_config_version
from .  import logger as e_logger
from .gcd       import GCD

log = logging.getLogger(__name__)

def run_protected():
    exit_code = 1
    try:
        app = Application()
        exit_code = app.run()
    except SystemExit as e:
        exit_code = e.args[0]
    except BaseException:
        exit_code = 1
        e_logger.fatal_exception()
    return exit_code


class Application(qt_core.QObject):
    def __init__(self):
        super().__init__()
        self._check_environment()
        self._exit_code = 0
        e_config_local.parse_command_line()
        e_config_local.parse_user_config()
        e_logger.turn_logger(True)


    def __del__(self):
        # TODO asserts for normal self.run() termination
        pass


    def run(self):
        gcd = GCD(silent_mode=e_config_local.silent_mode())
        if e_config_local.is_gui():
            from .ui import gui
            app = gui.run(gcd)
        else:
            from .ui import cui
            app = cui.run(gcd)
        gcd.start_threads(app)
        self._exit_code = gcd.exec_()
        gcd.release()
        e_logger.turn_logger(False)

        if self._exit_code == 0:
            log.info(
                "%s terminated successfully.",
                e_config_version.CLIENT_NAME)
        else:
            log.warning(
                "%s terminated with error.",
                e_config_version.CLIENT_NAME)
        return self._exit_code
    
    def _check_environment(self):
        if sys.version_info[:3] < e_config_version.PYTHON_MINIMAL_VERSION:
            raise RuntimeError(
                qt_core.QObject.tr("{} requires Python version {}.{}.{} or above. "
                "Current Python version is {}.{}.{}."
                .format(
                    e_config_version.CLIENT_NAME,
                    e_config_version.PYTHON_MINIMAL_VERSION[0],
                    e_config_version.PYTHON_MINIMAL_VERSION[1],
                    e_config_version.PYTHON_MINIMAL_VERSION[2],
                    sys.version_info[0],
                    sys.version_info[1],
                    sys.version_info[2])))

