# JOK
import argparse

import bmnclient.version

ARGUMENTS = None


def parse(argv) -> None:
    global ARGUMENTS

    # TODO sync decorations/names/description with server cli, append qsTr()
    parser = argparse.ArgumentParser(
        prog=argv[0],
        description=bmnclient.version.NAME)
    parser.add_argument(
        "-u",
        "--ui",
        action="store",
        nargs=1,
        default="auto",
        choices=["auto", "cui", "gui"],
        help="select user interface type, the default value is \'auto\'")
    parser.add_argument(
        "-l",
        "--logfile",
        help="set file name for logging")
    parser.add_argument(
        '-d',
        '--debug_mode',
        default=False,
        dest='debug_mode',
        action='store_true')

    ARGUMENTS = parser.parse_args(argv[1:])


# TODO
def is_gui():
    return 'cui' not in ARGUMENTS.ui


# TODO
def log_file():
    return ARGUMENTS.logfile


# TODO
def debug_mode():
    return ARGUMENTS.debug_mode
