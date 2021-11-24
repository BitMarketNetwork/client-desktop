from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PySide6.QtCore import QFile, QUrl

from ..utils import NotImplementedInstance
from ..utils.class_property import classproperty
from ..version import ProductPaths

if TYPE_CHECKING:
    from typing import Final

try:
    from . import qrc
except ImportError:
    pass


def _resource_exists(path) -> bool:
    return QFile.exists(path)


class Resources(NotImplementedInstance):
    if _resource_exists(":/images"):
        _ICON_FILE_PATH: Final = ":/images/icon-logo.svg"
    else:
        _ICON_FILE_PATH: Final = str(
            ProductPaths.RESOURCES_PATH / "images" / "icon-logo.svg")

    if _resource_exists(":/qml"):
        _QML_URL: Final = QUrl("qrc:///qml/")
    else:
        _QML_URL: Final = QUrl.fromLocalFile(
            str(ProductPaths.RESOURCES_PATH / "qml") + os.sep)

    if _resource_exists(":/translations"):
        _TRANSLATIONS_PATH: Final = ":/translations"
    else:
        _TRANSLATIONS_PATH: Final = str(
            ProductPaths.RESOURCES_PATH / "translations")

    @classproperty
    def iconFilePath(cls) -> str:  # noqa
        return cls._ICON_FILE_PATH

    @classproperty
    def qmlUrl(cls) -> QUrl:  # noqa
        return cls._QML_URL

    @classproperty
    def translationsPath(cls) -> str:  # noqa
        return cls._TRANSLATIONS_PATH
