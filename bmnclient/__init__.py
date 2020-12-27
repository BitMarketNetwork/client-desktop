# JOK+
import sys
from typing import List

from . import version, command_line, logger
from .ui.gui import Application

if sys.version_info[:3] < version.PYTHON_MINIMAL_VERSION:
    raise RuntimeError(
        "{} requires Python version {}.{}.{} or above. "
        "Current Python version is {}.{}.{}."
        .format(
            version.NAME,
            version.PYTHON_MINIMAL_VERSION[0],
            version.PYTHON_MINIMAL_VERSION[1],
            version.PYTHON_MINIMAL_VERSION[2],
            sys.version_info[0],
            sys.version_info[1],
            sys.version_info[2]))


def main(argv: List[str]) -> int:
    try:
        command_line.parse(argv)
        logger.configure(command_line.log_file())
        exit_code = Application(argv).run()
    except SystemExit as e:
        exit_code = e.args[0]
    except BaseException:
        exit_code = 1
        logger.fatalException()
    return exit_code
