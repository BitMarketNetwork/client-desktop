
import logging
import PySide2.QtCore as qt_core
log = logging.getLogger(__name__)


class RateSource(qt_core.QObject):

    def __init__(self, parent, **kwargs):
        super().__init__(parent=parent)
        self._name = kwargs["name"]
        self._api_url = kwargs["url"]

    @qt_core.Property(str, constant=True)
    def name(self):
        return self._name

    @qt_core.Property(str, constant=True)
    def apiUrl(self):
        return self._api_url

    def __str__(self):
        return f"{self._name}"
