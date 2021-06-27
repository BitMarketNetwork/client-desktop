from __future__ import annotations

from typing import TYPE_CHECKING

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication

from .system_tray import SystemTrayIcon
from ..application import CoreApplication
from ..version import Timer

if TYPE_CHECKING:
    from typing import Callable, Iterable, Optional
    from PySide2.QtGui import QClipboard, QFont, QWindow
    from ..application import CommandLine
    MessageType = CoreApplication.MessageType


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

    @property
    def systemTrayIcon(self) -> SystemTrayIcon:
        return self._system_tray_icon

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

    def showMessage(
            self,
            *,
            type_: MessageType = CoreApplication.MessageType.INFORMATION,
            title: Optional[str] = None,
            text: str,
            timeout: int = Timer.UI_MESSAGE_TIMEOUT) -> None:
        if type_ == CoreApplication.MessageType.INFORMATION:
            icon = self._system_tray_icon.MessageIcon.INFORMATION
        elif type_ == CoreApplication.MessageType.WARNING:
            icon = self._system_tray_icon.MessageIcon.WARNING
        elif type_ == CoreApplication.MessageType.ERROR:
            icon = self._system_tray_icon.MessageIcon.ERROR
        else:
            icon = self._system_tray_icon.MessageIcon.INFORMATION

        self._system_tray_icon.showMessage(title, text, icon, timeout)
