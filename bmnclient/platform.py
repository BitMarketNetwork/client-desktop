# JOK+
import os
import sys
from enum import Enum, auto
from pathlib import Path, PurePath

from bmnclient import version


class Platform(Enum):
    UNKNOWN = auto()
    WINDOWS = auto()
    DARWIN = auto()
    LINUX = auto()


# Detect platform
if sys.platform.startswith("win32"):
    CURRENT_PLATFORM = Platform.WINDOWS
elif sys.platform.startswith("darwin"):
    CURRENT_PLATFORM = Platform.DARWIN
elif sys.platform.startswith("linux"):
    CURRENT_PLATFORM = Platform.LINUX
else:
    CURRENT_PLATFORM = Platform.UNKNOWN
    raise RuntimeError("Unsupported platform \"{}\".".format(sys.platform))

# Detect system paths
USER_HOME_PATH = Path.home()
if CURRENT_PLATFORM == Platform.WINDOWS:
    USER_CONFIG_PATH = os.environ.get("APPDATA")
    if USER_CONFIG_PATH is None:
        raise RuntimeError("Can't determine APPDATA directory.")

    USER_CONFIG_PATH = PurePath(USER_CONFIG_PATH)
    USER_APPLICATION_CONFIG_PATH = \
        USER_CONFIG_PATH / \
        version.NAME
elif CURRENT_PLATFORM == Platform.DARWIN:
    USER_CONFIG_PATH = USER_HOME_PATH / "Library" / "Application Support"
    USER_APPLICATION_CONFIG_PATH = \
        USER_CONFIG_PATH / \
        version.NAME
elif CURRENT_PLATFORM == Platform.LINUX:
    USER_CONFIG_PATH = USER_HOME_PATH / ".config"
    USER_APPLICATION_CONFIG_PATH = \
        USER_CONFIG_PATH / \
        version.SHORT_NAME.lower()
else:
    raise RuntimeError("Can't determine user directories.")
