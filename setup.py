#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import setuptools
from setuptools.config import read_configuration

if TYPE_CHECKING:
    from typing import Dict, Final, List


METADATA: Final = read_configuration("setup.cfg")["metadata"]
PACKAGE_NAME: Final = METADATA["name"]


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
        include=(
            PACKAGE_NAME,
            PACKAGE_NAME + ".*"
        ),
        exclude=(
            PACKAGE_NAME + ".resources.qrc",
        )
    ),
    include_package_data=False,
    package_data=find_package_data({
        PACKAGE_NAME + ".resources": [
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
        "gui_scripts": [
            "bmn-client" + "=" + PACKAGE_NAME + ":main"
        ],
        "console_scripts": [
            "bmn-client_debug" + "=" + PACKAGE_NAME + ":main"
        ]
    },
    python_requires=">= 3.7, < 3.10"
)
