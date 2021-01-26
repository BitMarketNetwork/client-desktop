# JOK
import os

from PySide2.QtCore import QFile, QUrl

from ..version import Paths

try:
    from . import qrc
except ImportError:
    pass


def exists(path) -> bool:
    return QFile.exists(path)


if exists(":/images"):
    ICON_FILE_PATH = ":/images/icon-logo.svg"
else:
    ICON_FILE_PATH = Paths.RESOURCES_PATH / "images" / "icon-logo.svg"

if exists(":/qml"):
    QML_URL = QUrl("qrc:///qml/")
else:
    QML_URL = QUrl.fromLocalFile(str(Paths.RESOURCES_PATH / "qml") + os.sep)
