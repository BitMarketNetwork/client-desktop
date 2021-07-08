#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import setuptools
from setuptools.config import read_configuration

if TYPE_CHECKING:
    from typing import Dict, Final, List


PLATFORM_IS_WINDOWS: Final = sys.platform.startswith("win32")
PLATFORM_IS_DARWIN: Final = sys.platform.startswith("darwin")
PLATFORM_IS_LINUX: Final = sys.platform.startswith("linux")

METADATA: Final = read_configuration("setup.cfg")["metadata"]
NAME: Final = METADATA["name"]


def read_requirements(file_name: str) -> List[str]:
    with open(file_name) as f:
        return f.read().splitlines()


def find_package_data(
        package_data: Dict[str, List[str]]) -> Dict[str, List[str]]:
    result = {}
    for package_name, pattern_list in package_data.items():
        package_path = Path(package_name.replace(".", os.sep))
        result[package_name] = []
        for pattern in pattern_list:
            file_list = list(map(
                lambda p: str(p.relative_to(package_path)),
                package_path.glob(pattern)
            ))
            if not file_list:
                raise RuntimeError(
                    "package data '{1}' not found in package '{0}'".format(
                        package_name,
                        pattern))
            result[package_name].extend(file_list)
    return result


setuptools.setup(
    packages=setuptools.find_packages(
        exclude=(
            "tests",
            NAME + ".resources.qrc"
        )
    ),
    include_package_data=False,
    package_data=find_package_data({
        NAME + ".resources": [
            "images/**/*.svg",
            "images/**/*.icns",
            "images/**/*.ico",
            "qml/**/*.qml",
            "qml/**/qmldir",
            "translations/*.qm",
            "wordlist/*.txt",
        ]
    }),
    zip_safe=False,
    install_requires=read_requirements("requirements.txt"),
    entry_points={
        "gui_scripts" if PLATFORM_IS_WINDOWS else "console_scripts": [
            "bmn-client" + "=" + NAME + ":main"
        ]
    },
    python_requires=">= 3.7, <= 3.10"
)
