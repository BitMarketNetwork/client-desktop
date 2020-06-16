
import PySide2.QtCore as qt_core

class Style(qt_core.QObject):

    def __init__(self, parent, **kwargs):
        super().__init__(parent=parent)
        self._name = kwargs["name"]

    @qt_core.Property(str, constant=True)
    def name(self) -> str:
        return self._name
