# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

################################################################################

PLATFORM_WINDOWS = False
PLATFORM_DARWIN = False
PLATFORM_LINUX = False
if sys.platform.startswith("win32"):
    PLATFORM_WINDOWS = True
elif sys.platform.startswith("darwin"):
    PLATFORM_DARWIN = True
elif sys.platform.startswith("linux"):
    PLATFORM_LINUX = True
else:
    raise RuntimeError("unsupported platform '{}'".format(sys.platform))

if PLATFORM_WINDOWS:
    from PyInstaller.utils.win32.versioninfo import VSVersionInfo, \
        FixedFileInfo, StringFileInfo, StringTable, StringStruct, VarFileInfo, \
        VarStruct
elif PLATFORM_DARWIN:
    from PyInstaller.building.osx import BUNDLE

################################################################################
# Vars from Makefile
################################################################################

BASE_DIR = Path(os.getenv("BASE_DIR"))
CONTRIB_DIR = Path(os.getenv("CONTRIB_DIR"))
CONTRIB_PLATFORM_DIR = Path(os.getenv("CONTRIB_PLATFORM_DIR"))
PACKAGE_DIR = Path(os.getenv("PACKAGE_DIR"))
RESOURCES_DIR = Path(os.getenv("RESOURCES_DIR"))
DIST_DIR = Path(os.getenv("DIST_DIR"))
TEMP_DIR = Path(os.getenv("TEMP_DIR"))

TARGET_NAME_RELEASE = os.getenv("TARGET_NAME_RELEASE")
TARGET_NAME_DEBUG = os.getenv("TARGET_NAME_DEBUG")

BMN_PACKAGE_NAME = os.getenv("BMN_PACKAGE_NAME")
BMN_MAINTAINER = os.getenv("BMN_MAINTAINER")
BMN_MAINTAINER_DOMAIN = os.getenv("BMN_MAINTAINER_DOMAIN")
BMN_NAME = os.getenv("BMN_NAME")
BMN_SHORT_NAME = os.getenv("BMN_SHORT_NAME")
BMN_VERSION_STRING = os.getenv("BMN_VERSION_STRING")

if PLATFORM_WINDOWS:
    BMN_ICON_FILE_PATH = \
        Path(os.getenv("BMN_ICON_WINDOWS_FILE_PATH")).resolve()
elif PLATFORM_DARWIN:
    BMN_ICON_FILE_PATH = \
        Path(os.getenv("BMN_ICON_DARWIN_FILE_PATH")).resolve()
elif PLATFORM_LINUX:
    BMN_ICON_FILE_PATH = \
        Path(os.getenv("BMN_ICON_LINUX_FILE_PATH")).resolve()
else:
    BMN_ICON_FILE_PATH = None

USE_QRC = int(os.getenv("USE_QRC", "0"))

################################################################################

exclude_list = []
for file in (
        CONTRIB_DIR / "exclude_list",
        CONTRIB_PLATFORM_DIR / "exclude_list"):
    if file.exists():
        with open(file, "rt", encoding='utf-8') as f:
            for line in f:
                line = line.partition('#')[0].strip()
                if len(line) > 0:
                    exclude_list.append(line)

source_list = [
    (BASE_DIR / BMN_SHORT_NAME).resolve()
]

binary_list = [
]

data_path_list = [
    RESOURCES_DIR / "wordlist"
]
if USE_QRC != 1:
    data_path_list += [
        RESOURCES_DIR / "qml",
        RESOURCES_DIR / "images",
        RESOURCES_DIR / "translations"
    ]

hidden_imports = [
    'PySide2.QtQuick'
]


# Sync with NSIS
def create_version_info(file_name) -> Any:
    if not PLATFORM_WINDOWS:
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


analysis = Analysis(
    map(str, source_list),
    pathex=[],
    binaries=binary_list,
    datas=map(
        lambda x: (str(x.resolve()), str(x.relative_to(BASE_DIR))),
        data_path_list),
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    win_private_assemblies=False,
    win_no_prefer_redirects=False)

################################################################################


# TODO pathlib.PurePath.is_relative_to(), Python 3.9+
def is_relative_to(p1, p2) -> bool:
    try:
        return p1.relative_to(p2)
    except ValueError:
        return False


if PLATFORM_WINDOWS and False:
    os_root = Path(os.getenv("SystemRoot"))
    assert os_root.is_absolute() and os_root.is_dir()
    analysis.binaries = list(filter(
        lambda x: not is_relative_to(Path(x[1]), os_root),
        analysis.binaries))

# TODO temporary fix for Qt5Network
if PLATFORM_WINDOWS:
    for b in analysis.binaries.copy():
        if b[0].lower() == "libssl-1_1.dll":
            analysis.binaries.append(("libssl-1_1-x64.dll", b[1], b[2]))
        elif b[0].lower() == "libcrypto-1_1.dll":
            analysis.binaries.append(("libcrypto-1_1-x64.dll", b[1], b[2]))


def exclude_list_filter(v) -> bool:
    for pattern in exclude_list:
        path = Path(v[0])
        if fnmatch(str(path), pattern):
            print("Excluded file: " + v[0])
            return False
        elif PLATFORM_LINUX \
                and path.name.startswith("lib") \
                and len(path.name) > 3:
            pattern = pattern.split("/")
            if not pattern[-1].startswith("lib"):
                pattern[-1] = "lib" + pattern[-1]
                pattern = "/".join(pattern)
                if fnmatch(str(path), pattern):
                    print("Excluded file (lib): " + v[0])
                    return False
    return True


analysis.binaries = list(filter(exclude_list_filter, analysis.binaries))
analysis.datas = list(filter(exclude_list_filter, analysis.datas))

################################################################################


def save_file_list(suffix, file_list) -> None:
    with open(
            DIST_DIR / (BMN_SHORT_NAME + suffix),
            "wt",
            encoding='utf-8') as file:
        for f in sorted(file_list):
            file.write("{:<120} {}\n".format(f[0], f[1]))


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

if PLATFORM_DARWIN:
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
