# JOK
import sys

import bmnclient.command_line
import bmnclient.logger
import bmnclient.resources
import bmnclient.version as version
from bmnclient.gcd import GCD

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


def main(argv) -> int:
    bmnclient.command_line.parse(argv)
    exit_code = 1

    try:
        # TODO to application, level from command_line
        bmnclient.logger.configure(bmnclient.command_line.log_file())

        gcd = GCD(silent_mode=bmnclient.command_line.silent_mode())

        if bmnclient.command_line.is_gui():
            from .ui import gui
            app = gui.Application(gcd, argv)
        else:
            from .ui import cui
            app = cui.run(gcd)

        # TODO run in event loop
        gcd.start_threads(app)
        exit_code = gcd.app.runEventLoop()
        gcd.release()

    except SystemExit as e:
        exit_code = e.args[0]

    except BaseException:
        exit_code = 1
        bmnclient.logger.fatalException()

    return exit_code
