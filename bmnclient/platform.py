# JOK++
import os
import sys
from enum import Enum, auto
from pathlib import Path, PurePath
from typing import Final

from .version import Product


class Platform:
    class Type(Enum):
        UNKNOWN = auto()
        WINDOWS = auto()
        DARWIN = auto()
        LINUX = auto()

    if sys.platform.startswith("win32"):
        TYPE: Final = Type.WINDOWS
    elif sys.platform.startswith("darwin"):
        TYPE: Final = Type.DARWIN
    elif sys.platform.startswith("linux"):
        TYPE: Final = Type.LINUX
    else:
        TYPE: Final = Type.UNKNOWN
        raise RuntimeError("Unsupported platform \"{}\".".format(sys.platform))

    @classmethod
    def isWindows(cls) -> bool:
        return cls.TYPE == cls.Type.WINDOWS

    @classmethod
    def isDarwin(cls) -> bool:
        return cls.TYPE == cls.Type.DARWIN

    @classmethod
    def isLinux(cls) -> bool:
        return cls.TYPE == cls.Type.LINUX


def _userConfigPath(user_home_path: PurePath) -> PurePath:
    if Platform.isWindows():
        v = os.environ.get("APPDATA")
        if not v:
            raise RuntimeError("Can't determine APPDATA directory.")
        return PurePath(v)
    elif Platform.isDarwin():
        return user_home_path / "Library" / "Application Support"
    elif Platform.isLinux():
        return user_home_path / ".config"
    else:
        raise RuntimeError("Can't determine user directories.")


def _userApplicationConfigPath(user_config_path: PurePath) -> PurePath:
    if Platform.isWindows():
        return user_config_path / Product.NAME
    elif Platform.isDarwin():
        return user_config_path / Product.NAME
    elif Platform.isLinux():
        return user_config_path / Product.SHORT_NAME.lower()
    else:
        raise RuntimeError("Can't determine user directories.")


class PlatformPaths:
    USER_HOME_PATH: Final = \
        Path.home()
    USER_CONFIG_PATH: Final = \
        _userConfigPath(USER_HOME_PATH)
    USER_APPLICATION_CONFIG_PATH: Final = \
        _userApplicationConfigPath(USER_CONFIG_PATH)
