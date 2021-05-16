# JOK4
from __future__ import annotations

import os
import sys
from enum import auto, Enum
from pathlib import Path
from typing import TYPE_CHECKING

from .utils import NotImplementedInstance
from .utils.class_property import classproperty
from .version import Product

if TYPE_CHECKING:
    from typing import Final
    from pathlib import PurePath


class Platform(NotImplementedInstance):
    class Type(Enum):
        UNKNOWN: Final = auto()
        WINDOWS: Final = auto()
        DARWIN: Final = auto()
        LINUX: Final = auto()

    if sys.platform.startswith("win32"):
        _TYPE: Final = Type.WINDOWS
    elif sys.platform.startswith("darwin"):
        _TYPE: Final = Type.DARWIN
    elif sys.platform.startswith("linux"):
        _TYPE: Final = Type.LINUX
    else:
        _TYPE: Final = Type.UNKNOWN
        raise RuntimeError("unsupported platform '{}'".format(sys.platform))

    @classproperty
    def type(cls) -> Type:  # noqa
        return cls._TYPE

    @classproperty
    def isWindows(cls) -> bool:  # noqa
        return cls._TYPE == cls.Type.WINDOWS

    @classproperty
    def isDarwin(cls) -> bool:  # noqa
        return cls._TYPE == cls.Type.DARWIN

    @classproperty
    def isLinux(cls) -> bool:  # noqa
        return cls._TYPE == cls.Type.LINUX


def _userConfigPath(user_home_path: PurePath) -> PurePath:
    if Platform.isWindows:
        v = os.environ.get("APPDATA")
        if not v:
            raise RuntimeError("can't determine APPDATA directory")
        return PurePath(v)
    elif Platform.isDarwin:
        return user_home_path / "Library" / "Application Support"
    elif Platform.isLinux:
        return user_home_path / ".config"
    else:
        raise RuntimeError("can't determine user directories")


def _userApplicationConfigPath(user_config_path: PurePath) -> PurePath:
    if Platform.isWindows:
        return user_config_path / Product.NAME
    elif Platform.isDarwin:
        return user_config_path / Product.NAME
    elif Platform.isLinux:
        return user_config_path / Product.SHORT_NAME.lower()
    else:
        raise RuntimeError("can't determine user directories")


class PlatformPaths(NotImplementedInstance):
    _USER_HOME_PATH: Final = \
        Path.home()
    _USER_CONFIG_PATH: Final = \
        _userConfigPath(_USER_HOME_PATH)
    _USER_APPLICATION_CONFIG_PATH: Final = \
        _userApplicationConfigPath(_USER_CONFIG_PATH)

    @classproperty
    def userHomePath(cls) -> PurePath:  # noqa
        return cls._USER_HOME_PATH

    @classproperty
    def userConfigPath(cls) -> PurePath:  # noqa
        return cls._USER_CONFIG_PATH

    @classproperty
    def userApplicationConfigPath(cls) -> PurePath:  # noqa
        return cls._USER_APPLICATION_CONFIG_PATH
