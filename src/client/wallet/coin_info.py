import logging

import PySide2.QtCore as qt_core

log = logging.getLogger(__name__)


class CoinInfo(qt_core.QObject):

    def __init__(self, name,  parent, **kwargs):
        super().__init__(parent=parent)
        self._name = name
        self._version_str, self._version_num = kwargs["version"]
        self._height = kwargs["height"]
        self._online = kwargs["status"]

    @qt_core.Property(str, constant=True)
    def name(self) -> str:
        return self._name

    @qt_core.Property(str, constant=True)
    def versionHuman(self) -> str:
        return self._version_str

    @qt_core.Property(str, constant=True)
    def versionNum(self) -> str:
        return str(self._version_num)

    @qt_core.Property(str, constant=True)
    def height(self) -> str:
        return str(self._height)

    @qt_core.Property(bool, constant=True)
    def online(self) -> bool:
        return self._online

    def __str__(self) -> str:
        return self._name
