# Only standard imports, used by Makefile, setup.cfg.
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List, Optional

from .version import Product

__version__ = Product.VERSION_STRING


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv

    if sys.version_info[:3] < Product.PYTHON_MINIMAL_VERSION:
        raise RuntimeError(
            "{} requires Python version {}.{}.{} or above, "
            "current Python version is {}.{}.{}"
            .format(
                Product.NAME,
                *Product.PYTHON_MINIMAL_VERSION[:3],
                *sys.version_info[:3]))

    try:
        from .application import CommandLine
        from .logger import Logger
        from .ui.qml import QmlApplication
    except ImportError:
        raise RuntimeError("requirements not installed")

    try:
        command_line = CommandLine(argv)
        Logger.configure(command_line.logFilePath, command_line.logLevel)
        exit_code = QmlApplication(command_line=command_line).run()
    except SystemExit as e:
        exit_code = e.args[0]
    return exit_code
