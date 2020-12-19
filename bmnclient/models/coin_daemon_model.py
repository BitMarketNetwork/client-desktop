# JOK
import PySide2.QtCore as QtCore

from bmnclient.wallet import coins


class CoinDaemonModel(QtCore.QObject):
    def __init__(self, coin, parent=None, **kwargs):
        super().__init__(parent=parent)

        self._coin = coin

        try:
            self._version_string = str(kwargs["version"][0])
            self._version = int(kwargs["version"][1])
        except (LookupError, TypeError, ValueError):
            self._version_string = "unknown"
            self._version = -1
        try:
            self._height = int(kwargs["height"])
        except (LookupError, TypeError, ValueError):
            self._height = -1
        try:
            self._status = int(kwargs["status"])
        except (LookupError, TypeError, ValueError):
            self._status = -1

    @QtCore.Property(coins.CoinType, constant=True)
    def coin(self):
        return self._coin

    @QtCore.Property(str, constant=True)
    def versionString(self):
        return self._version_string

    @QtCore.Property(int, constant=True)
    def version(self):
        return self._version

    @QtCore.Property(int, constant=True)
    def height(self):
        return self._height

    @QtCore.Property(int, constant=True)
    def status(self):
        return self._status
