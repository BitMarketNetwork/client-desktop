# -*- mode: python ; coding: utf-8 -*-

from __future__ import annotations

import importlib.util
import os
import sys
from fnmatch import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING

# noinspection PyPackageRequirements
from PyInstaller.building.build_main import \
    Analysis, \
    COLLECT, \
    EXE, \
    PYZ

if TYPE_CHECKING:
    from typing import Any, Final, List, Tuple


################################################################################
# Platform
################################################################################


PLATFORM_IS_WINDOWS: Final = sys.platform.startswith("win32")
PLATFORM_IS_DARWIN: Final = sys.platform.startswith("darwin")
PLATFORM_IS_LINUX: Final = sys.platform.startswith("linux")

if PLATFORM_IS_WINDOWS:
    # noinspection PyPackageRequirements
    from PyInstaller.utils.win32.versioninfo import \
        FixedFileInfo, \
        StringFileInfo, \
        StringStruct, \
        StringTable, \
        VarFileInfo, \
        VarStruct, \
        VSVersionInfo
elif PLATFORM_IS_DARWIN:
    # noinspection PyPackageRequirements
    from PyInstaller.building.osx import BUNDLE
elif PLATFORM_IS_LINUX:
    pass
else:
    raise RuntimeError("unsupported platform '{}'".format(sys.platform))


################################################################################
# Utils
################################################################################


def get_module_path(name: str) -> Path:
    spec = importlib.util.find_spec(name)
    if not spec:
        raise ImportError("module '{}' not found".format(name))

    if (
            not spec.submodule_search_locations
            or not spec.submodule_search_locations[0]
            or not Path(spec.submodule_search_locations[0]).exists()
    ):
        raise FileNotFoundError("path of module '{}' not found".format(name))

    return Path(spec.submodule_search_locations[0])


def glob_strict(path: Path, pattern: str) -> List[Path]:
    if not path.is_dir():
        raise FileNotFoundError("path '{}' not found".format(str(path)))
    result = list(path.glob(pattern))
    if not result:
        raise FileNotFoundError(
            "can't find files matching pattern '{}', path '{}'"
            .format(pattern, str(path)))
    return result


def load_exclude_list() -> str:
    for file in (
            CONTRIB_PATH / "exclude_list",
            CONTRIB_PLATFORM_PATH / "exclude_list"):
        if file.exists():
            with open(file, "rt", encoding='utf-8') as f:
                for line in f:
                    line = line.partition('#')[0].strip()
                    if len(line) > 0:
                        yield line


def exclude_list_filter(v) -> bool:
    for pattern in exclude_list:
        path = Path(v[0])
        if fnmatch(str(path), pattern):
            print("Excluded file: " + v[0])
            return False
        elif (
                (PLATFORM_IS_LINUX or PLATFORM_IS_DARWIN)
                and path.name.startswith("lib")
                and len(path.name) > 3
        ):
            pattern = pattern.split("/")
            if not pattern[-1].startswith("lib"):
                pattern[-1] = "lib" + pattern[-1]
                pattern = "/".join(pattern)
                if fnmatch(str(path), pattern):
                    print("Excluded file (lib): " + v[0])
                    return False
    return True


def save_file_list(suffix, file_list) -> None:
    with open(
            DIST_PATH / (BMN_SHORT_NAME + suffix),
            "wt",
            encoding='utf-8') as file:
        for f in sorted(file_list):
            file.write("{:<120} {}\n".format(f[0], f[1]))


# TODO pathlib.PurePath.is_relative_to(), Python 3.9+
def is_relative_to(p1, p2) -> bool:
    try:
        return p1.relative_to(p2)
    except ValueError:
        return False


def find_qt_wayland_plugins() -> List[Tuple[Path, Path]]:
    if not PLATFORM_IS_LINUX:
        return []
    result = []
    module_path = get_module_path("PySide6")

    for name in (
            "wayland-decoration-client",
            "wayland-graphics-integration-client",
            "wayland-shell-integration"
    ):
        relative_path = Path("Qt") / "plugins" / name
        for file_path in glob_strict(module_path / relative_path, "lib*.so"):
            result.append((file_path, Path("PySide6") / relative_path))

    assert result
    return result


# Sync with NSIS
def create_version_info(file_name) -> Any:
    if not PLATFORM_IS_WINDOWS:
        return None
    version_tuple = tuple(
        map(int, (BMN_VERSION_STRING + ".0").split('.', maxsplit=4)))
    return VSVersionInfo(
        ffi=FixedFileInfo(
            filevers=version_tuple,
            prodvers=version_tuple,
            mask=0x0,
            flags=0x0,
            OS=0x4,
            fileType=0x1,
            subtype=0x0,
            date=(0, 0)
        ),
        kids=[
            StringFileInfo([
                StringTable(
                    "040904b0", [
                        StringStruct(
                            "FileDescription",
                            BMN_NAME),
                        StringStruct(
                            "FileVersion",
                            BMN_VERSION_STRING),
                        StringStruct(
                            "OriginalFilename",
                            file_name),
                        StringStruct(
                            "ProductName",
                            BMN_NAME),
                        StringStruct(
                            "ProductVersion",
                            BMN_VERSION_STRING),
                        StringStruct(
                            "CompanyName",
                            BMN_MAINTAINER),
                        StringStruct(
                            "LegalCopyright",
                            f"© {BMN_MAINTAINER}. All rights reserved.")
                    ])
            ]),
            VarFileInfo([
                VarStruct("Translation", [1033, 1200])
            ])
        ])


################################################################################
# Vars from Makefile
################################################################################


BASE_PATH: Final = Path(os.getenv("BASE_DIR"))
CONTRIB_PATH: Final = Path(os.getenv("CONTRIB_DIR"))
CONTRIB_PLATFORM_PATH: Final = Path(os.getenv("CONTRIB_PLATFORM_DIR"))
PACKAGE_PATH: Final = Path(os.getenv("PACKAGE_DIR"))
RESOURCES_PATH: Final = Path(os.getenv("RESOURCES_DIR"))
DIST_PATH: Final = Path(os.getenv("DIST_DIR"))
BUILD_PATH: Final = Path(os.getenv("BUILD_DIR"))

TARGET_NAME_RELEASE: Final = os.getenv("TARGET_NAME_RELEASE")
TARGET_NAME_DEBUG: Final = os.getenv("TARGET_NAME_DEBUG")

BMN_PACKAGE_NAME: Final = os.getenv("BMN_PACKAGE_NAME")
BMN_MAINTAINER: Final = os.getenv("BMN_MAINTAINER")
BMN_MAINTAINER_DOMAIN: Final = os.getenv("BMN_MAINTAINER_DOMAIN")
BMN_NAME: Final = os.getenv("BMN_NAME")
BMN_SHORT_NAME: Final = os.getenv("BMN_SHORT_NAME")
BMN_VERSION_STRING: Final = os.getenv("BMN_VERSION_STRING")

if PLATFORM_IS_WINDOWS:
    BMN_ICON_FILE_PATH: Final = \
        Path(os.getenv("BMN_ICON_WINDOWS_FILE_PATH")).resolve()
elif PLATFORM_IS_DARWIN:
    BMN_ICON_FILE_PATH: Final = \
        Path(os.getenv("BMN_ICON_DARWIN_FILE_PATH")).resolve()
elif PLATFORM_IS_LINUX:
    BMN_ICON_FILE_PATH: Final = \
        Path(os.getenv("BMN_ICON_LINUX_FILE_PATH")).resolve()
else:
    BMN_ICON_FILE_PATH: Final = None

USE_QRC: Final = int(os.getenv("USE_QRC", "0"))


################################################################################
# Lists
################################################################################


exclude_list = [
    *load_exclude_list()
]

source_list = [
    (CONTRIB_PATH / "main.py").resolve()
]

binary_list = [
    *find_qt_wayland_plugins()
]

data_path_list = [
    RESOURCES_PATH / "wordlist"
]
if USE_QRC != 1:
    data_path_list += [
        RESOURCES_PATH / "qml",
        RESOURCES_PATH / "images",
        RESOURCES_PATH / "translations"
    ]

hidden_import_list = [
    "PySide6.QtQuick"
]


################################################################################
# PyInstaller Run
################################################################################


analysis = Analysis(
    map(str, source_list),
    pathex=[],
    binaries=map(lambda v: map(str, v), binary_list),
    datas=map(
        lambda x: (str(x.resolve()), str(x.relative_to(BASE_PATH))),
        data_path_list),
    hiddenimports=hidden_import_list,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    win_private_assemblies=False,
    win_no_prefer_redirects=False)


################################################################################


if PLATFORM_IS_WINDOWS and False:
    os_root = Path(os.getenv("SystemRoot"))
    assert os_root.is_absolute() and os_root.is_dir()
    analysis.binaries = list(filter(
        lambda x: not is_relative_to(Path(x[1]), os_root),
        analysis.binaries))

analysis.binaries = list(filter(exclude_list_filter, analysis.binaries))
analysis.datas = list(filter(exclude_list_filter, analysis.datas))


################################################################################


save_file_list(".datas", analysis.datas)
save_file_list(".binaries", analysis.binaries)
save_file_list(".scripts", analysis.scripts)


################################################################################


pyz = PYZ(
    analysis.pure,
    analysis.zipped_data)


################################################################################


exe_release = EXE(
    pyz,
    analysis.scripts,
    bootloader_ignore_signals=False,
    console=False,
    debug=False,
    name=TARGET_NAME_RELEASE,
    exclude_binaries=True,
    icon=str(BMN_ICON_FILE_PATH),
    version=create_version_info(TARGET_NAME_RELEASE),
    strip=False,
    upx=False)

exe_debug = EXE(
    pyz,
    analysis.scripts,
    bootloader_ignore_signals=False,
    console=True,
    debug=True,
    name=TARGET_NAME_DEBUG,
    exclude_binaries=True,
    icon=str(BMN_ICON_FILE_PATH),
    version=create_version_info(TARGET_NAME_DEBUG),
    strip=False,
    upx=False)


################################################################################


collect = COLLECT(
    exe_release,
    exe_debug,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=BMN_SHORT_NAME)  # Sync with Makefile:DIST_SOURCE_DIR

if PLATFORM_IS_DARWIN:
    bundle_identifier = \
        ".".join(BMN_MAINTAINER_DOMAIN.split('.')[::-1]) \
        + "." + BMN_SHORT_NAME
    bundle = BUNDLE(
        collect,
        name=BMN_NAME + ".app",
        version=BMN_VERSION_STRING,
        icon=str(BMN_ICON_FILE_PATH),
        bundle_identifier=bundle_identifier,
        # TODO
        # https://developer.apple.com/documentation/bundleresources/information_property_list
        info_plist={
            "NSPrincipalClass": "NSApplication",
            "NSAppleScriptEnabled": False,
            "NSHighResolutionCapable": True,
            "NSSupportsAutomaticGraphicsSwitching": True,
            "LSBackgroundOnly": False
        }
    )
