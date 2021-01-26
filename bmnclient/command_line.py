# JOK
import argparse

from .version import Product

ARGUMENTS = None


def parse(argv) -> None:
    global ARGUMENTS

    # TODO sync decorations/names/description with server cli, append qsTr()
    parser = argparse.ArgumentParser(
        prog=argv[0],
        description=Product.NAME)
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
def log_file():
    return ARGUMENTS.logfile


# TODO
def debug_mode():
    return ARGUMENTS.debug_mode
