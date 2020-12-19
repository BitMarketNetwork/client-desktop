
from typing import Optional
import PySide2.QtCore as qt_core


class Style(qt_core.QObject):

    def __init__(self, parent, name: str, value: Optional[str] = None):
        super().__init__(parent=parent)
        self.__name = name
        self.value = value or name

    @qt_core.Property(str, constant=True)
    def name(self) -> str:
        return self.__name
