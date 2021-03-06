# JOK
import os

from PySide2.QtCore import QFile, QUrl

from bmnclient import version

try:
    from . import qrc
except ImportError:
    pass


def exists(path) -> bool:
    return QFile.exists(path)


if exists(":/images"):
    ICON_FILE_PATH = ":/images/icon-logo.svg"
else:
    ICON_FILE_PATH = version.RESOURCES_PATH / "images" / "icon-logo.svg"

if exists(":/qml"):
    QML_URL = QUrl("qrc:///qml/")
else:
    QML_URL = QUrl.fromLocalFile(str(version.RESOURCES_PATH / "qml") + os.sep)
