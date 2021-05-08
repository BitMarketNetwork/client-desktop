# JOK4
from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from .application import CommandLine
from .logger import Logger
from .ui.gui import Application
from .version import Product

if TYPE_CHECKING:
    from typing import List

if sys.version_info[:3] < Product.PYTHON_MINIMAL_VERSION:
    raise RuntimeError(
        "{} requires Python version {}.{}.{} or above, "
        "current Python version is {}.{}.{}"
        .format(
            Product.NAME,
            Product.PYTHON_MINIMAL_VERSION[0],
            Product.PYTHON_MINIMAL_VERSION[1],
            Product.PYTHON_MINIMAL_VERSION[2],
            sys.version_info[0],
            sys.version_info[1],
            sys.version_info[2]))


def main(argv: List[str]) -> int:
    try:
        CommandLine.parse(argv)
        Logger.configure(
            CommandLine.logFilePath,
            logging.DEBUG if CommandLine.isDebugMode else logging.INFO)
        exit_code = Application(argv).run()
    except SystemExit as e:
        exit_code = e.args[0]
    except Exception:  # noqa
        exit_code = 1
        Logger.fatalException()
    return exit_code
