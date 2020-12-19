
import PySide2.QtCore as qt_core

class BaseUnit(qt_core.QObject):

    def __init__(self, name: str, factor: int, parent: qt_core.QObject):
        super().__init__(parent=parent)
        self._name = name
        self._factor = factor

    @qt_core.Property(str, constant=True)
    def name(self) -> str:
        return self._name

    @property
    def factor(self) -> int:
        return self._factor
