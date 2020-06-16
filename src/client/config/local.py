import argparse

from . import version as e_config_version


COMMAND_LINE = None
USER_CONFIG = None


def parse_command_line():
    global COMMAND_LINE

    parser = argparse.ArgumentParser(
        description=e_config_version.CLIENT_NAME)
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
        "--style",
        nargs=argparse.REMAINDER,
        help="Handle styles")
    parser.add_argument(
        '-s', 
        '--silent_mode', 
        default=False,
        dest='silent_mode', 
        action='store_true')

    COMMAND_LINE = parser.parse_args()

def is_gui():
    global COMMAND_LINE
    return 'cui' not in COMMAND_LINE.ui 

def log_file():
    global COMMAND_LINE
    return COMMAND_LINE.logfile

def silent_mode():
    global COMMAND_LINE
    return COMMAND_LINE.silent_mode


def parse_user_config():
    # TODO
    pass
