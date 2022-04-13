# -*- mode: python ; coding: utf-8 -*-

from __future__ import annotations

import importlib.util
import os
import sys
from fnmatch import fnmatch
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING

# noinspection PyPackageRequirements
from PyInstaller.building.build_main import \
    Analysis, \
    COLLECT, \
    EXE, \
    PYZ

if TYPE_CHECKING:
    from typing import Any, Dict, Final, List, Tuple, Iterable


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


def glob_strict(path: Path, pattern_list: Iterable[str]) -> List[Path]:
    if not path.is_dir():
        raise FileNotFoundError("path '{}' not found".format(str(path)))
    result = list(chain.from_iterable(path.glob(p) for p in pattern_list))
    if not result:
        raise FileNotFoundError(
            "can't find files matching patterns '{}', path '{}'"
            .format(", ".join(pattern_list), str(path)))
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


def exclude_list_filter(file_item: List[str, str]) -> bool:
    file_path = Path(file_item[0])
    for pattern in exclude_list:
        if fnmatch(str(file_path), pattern):
            print("Excluded file: " + str(file_path))
            return False
        elif (
                (PLATFORM_IS_LINUX or PLATFORM_IS_DARWIN)
                and file_path.name.startswith("lib")
                and len(file_path.name) > 3
        ):
            pattern = pattern.split("/")
            if not pattern[-1].startswith("lib"):
                pattern[-1] = "lib" + pattern[-1]
                pattern = "/".join(pattern)
                if fnmatch(str(file_path), pattern):
                    print("Excluded file (lib): " + str(file_path))
                    return False
    return True


def qt_translations_filter(file_item: List[str, str]) -> bool:
    file_path = Path(file_item[0])
    if (
            not fnmatch(file_path, PYSIDE_PATH.name + "/Qt/translations/*")
            and not fnmatch(file_path, PYSIDE_PATH.name + "/translations/*")
    ):
        return True

    for name in BMN_TRANSLATION_LIST.split(" "):
        name = name.strip()
        if not name:
            continue
        language, _ = name.split("_")
        if (
                fnmatch(file_path.name, f"*_{language}.*")
                or fnmatch(file_path.name, f"*_{name}.*")
        ):
            return True
    print("Excluded file (translation): " + str(file_path))
    return False


def save_file_list(suffix: str, file_list: List[List[str, str]]) -> None:
    with open(
            DIST_PATH / (BMN_SHORT_NAME + suffix),
            "wt",
            encoding='utf-8') as file:
        for f in sorted(file_list):
            file.write("{:<120} {}\n".format(f[0], f[1]))


# TODO pathlib.PurePath.is_relative_to(), Python 3.9+
def is_relative_to(p1: Path, p2: Path) -> bool:
    try:
        p1.relative_to(p2)
        return True
    except ValueError:
        return False


def find_qt_plugins(
        plugins: Dict[Path, Tuple[str, ...]]) -> List[Tuple[Path, Path]]:
    result = []

    for plugin_path, mask_list in plugins.items():
        plugin_path = Path("Qt") / "plugins" / plugin_path
        for file_path in glob_strict(PYSIDE_PATH / plugin_path, mask_list):
            result.append((file_path, PYSIDE_PATH.name / plugin_path))
    assert not plugins or result
    return result


# Sync with NSIS
def create_version_info(file_name: str) -> Any:
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
PYSIDE_PATH: Final = get_module_path("PySide6")
TARGET_NAME_RELEASE: Final = os.getenv("TARGET_NAME_RELEASE")
TARGET_NAME_DEBUG: Final = os.getenv("TARGET_NAME_DEBUG")

BMN_PACKAGE_NAME: Final = os.getenv("BMN_PACKAGE_NAME")
BMN_MAINTAINER: Final = os.getenv("BMN_MAINTAINER")
BMN_MAINTAINER_DOMAIN: Final = os.getenv("BMN_MAINTAINER_DOMAIN")
BMN_NAME: Final = os.getenv("BMN_NAME")
BMN_SHORT_NAME: Final = os.getenv("BMN_SHORT_NAME")
BMN_VERSION_STRING: Final = os.getenv("BMN_VERSION_STRING")
BMN_TRANSLATION_LIST: Final = os.getenv("BMN_TRANSLATION_LIST")

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

binary_list = []
if PLATFORM_IS_LINUX:
    binary_list += [
        *find_qt_plugins({
            Path("wayland-decoration-client"): (
                "lib*.so",
            ),
            Path("wayland-graphics-integration-client"): (
                "lib*.so",
            ),
            Path("wayland-shell-integration"): (
                "lib*.so",
            ),
        }),
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
    "cffi"
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
analysis.binaries = list(filter(qt_translations_filter, analysis.binaries))
analysis.datas = list(filter(exclude_list_filter, analysis.datas))
analysis.datas = list(filter(qt_translations_filter, analysis.datas))


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
