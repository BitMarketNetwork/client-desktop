# Only standard imports, used by Makefile, setup.cfg.
from __future__ import annotations

from typing import TYPE_CHECKING

from .version import Product

if TYPE_CHECKING:
    from typing import List, Optional

__version__ = Product.VERSION_STRING


def main(argv: Optional[List[str]] = None) -> int:
    import sys

    if sys.version_info[:3] < Product.PYTHON_MINIMAL_VERSION:
        raise RuntimeError(
            "{} requires Python version {}.{}.{} or above, "
            "current Python version is {}.{}.{}".format(
                Product.NAME,
                *Product.PYTHON_MINIMAL_VERSION[:3],
                *sys.version_info[:3],
            )
        )

    if argv is None:
        argv = sys.argv

    from .debug import Debug

    Debug.setState("-d" in argv or "--debug" in argv)

    from .application import CommandLine
    from .logger import Logger
    from .ui.qml import QmlApplication

    command_line = CommandLine(argv)
    Logger.configure(command_line.logFilePath, command_line.logLevel)
    return QmlApplication(command_line=command_line).run()
