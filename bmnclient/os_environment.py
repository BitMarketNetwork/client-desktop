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


def _configPath(home_path: Path) -> Path:
    if Platform.isWindows:
        v = os.environ.get("APPDATA")
        if not v:
            raise RuntimeError("can't determine APPDATA directory")
        return Path(v)
    elif Platform.isDarwin:
        return home_path / "Library" / "Preferences"
    elif Platform.isLinux:
        return home_path / ".config"
    else:
        raise RuntimeError("can't determine config directories")

def _localDataPath(home_path: Path) -> Path:
    if Platform.isWindows:
        v = os.environ.get("LOCALAPPDATA")
        if not v:
            raise RuntimeError("can't determine LOCALAPPDATA directory")
        return Path(v)
    elif Platform.isDarwin:
        return home_path / "Library" / "Application Support"
    elif Platform.isLinux:
        return home_path / ".local" / "share"
    else:
        raise RuntimeError("can't determine local data directories")


def _applicationConfigPath(config_path: Path) -> Path:
    if Platform.isWindows:
        return config_path / Product.NAME
    elif Platform.isDarwin:
        return config_path / Product.NAME
    elif Platform.isLinux:
        return config_path / Product.SHORT_NAME.lower()
    else:
        raise RuntimeError("can't determine config directories")

def _applicationLocalDataPath(local_data_path: Path) -> Path:
    if Platform.isWindows:
        return local_data_path / Product.NAME
    elif Platform.isDarwin:
        return local_data_path / Product.NAME
    elif Platform.isLinux:
        return local_data_path / Product.SHORT_NAME.lower()
    else:
        raise RuntimeError("can't determine local storage directories")


class PlatformPaths(NotImplementedInstance):
    _HOME_PATH: Final = Path.home()
    _CONFIG_PATH: Final = _configPath(_HOME_PATH)
    _LOCAL_DATA_PATH: Final = _localDataPath(_HOME_PATH)
    _APPLICATION_CONFIG_PATH: Final = _applicationConfigPath(_CONFIG_PATH)
    _APPLICATION_LOCAL_DATA_PATH: Final = _applicationLocalDataPath(_LOCAL_DATA_PATH)

    @classproperty
    def homePath(cls) -> Path:  # noqa
        return cls._HOME_PATH

    @classproperty
    def configPath(cls) -> Path:  # noqa
        return cls._CONFIG_PATH

    @classproperty
    def applicationConfigPath(cls) -> Path:  # noqa
        return cls._APPLICATION_CONFIG_PATH

    @classproperty
    def applicationLocalDataPath(cls) -> Path:  # noqa
        return cls._APPLICATION_LOCAL_DATA_PATH
