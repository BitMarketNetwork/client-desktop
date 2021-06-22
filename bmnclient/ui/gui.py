# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication

from .system_tray import SystemTrayIcon
from ..application import CoreApplication

if TYPE_CHECKING:
    from typing import Callable, Iterable, Optional
    from PySide2.QtGui import QClipboard, QFont, QWindow
    from ..application import CommandLine


class GuiApplication(CoreApplication):
    def __init__(
            self,
            *,
            command_line: CommandLine,
            model_factory: Optional[Callable[[object], object]] = None) -> None:
        super().__init__(
            qt_class=QApplication,
            command_line=command_line,
            model_factory=model_factory)
        self._system_tray_icon = SystemTrayIcon(self)

    @property
    def defaultFont(self) -> QFont:
        return self._qt_application.font()

    @property
    def clipboard(self) -> QClipboard:
        return self._qt_application.clipboard()

    @property
    def isVisible(self) -> bool:
        return any(w.isVisible() for w in self.topLevelWindowList)

    @property
    def isActiveFocus(self) -> bool:
        return any(w.isActive() for w in self.topLevelWindowList)

    @property
    def topLevelWindowList(self) -> Iterable[QWindow]:
        return self._qt_application.topLevelWindows()

    def show(self, show: bool = True) -> None:
        for window in self.topLevelWindowList:
            if show:
                window.setVisible(True)
                # noinspection PyTypeChecker
                state = int(window.windowStates())
                if (state & Qt.WindowMinimized) == Qt.WindowMinimized:
                    window.show()
                window.raise_()
                window.requestActivate()
            else:
                window.setVisible(False)
