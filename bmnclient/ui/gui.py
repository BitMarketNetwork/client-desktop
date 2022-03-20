from __future__ import annotations

from os import environ
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from .system_tray import SystemTrayIcon
from ..application import CoreApplication
from ..os_environment import Platform
from ..version import Timer

if TYPE_CHECKING:
    from typing import Iterable, Optional
    from PySide6.QtGui import QClipboard, QFont, QWindow
    from ..application import CommandLine
    from ..coins.abstract import CoinModelFactory
    MessageType = CoreApplication.MessageType


class GuiApplication(CoreApplication):
    def __init__(
            self,
            *,
            command_line: CommandLine,
            model_factory: CoinModelFactory) -> None:

        # Warning: Ignoring XDG_SESSION_TYPE=wayland on Gnome. Use
        # QT_QPA_PLATFORM=wayland to run on Wayland anyway.
        if Platform.isLinux:
            if (
                    environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
                    and not environ.get("QT_QPA_PLATFORM")
            ):
                environ["QT_QPA_PLATFORM"] = "wayland"

        super().__init__(
            qt_class=QApplication,
            command_line=command_line,
            model_factory=model_factory)

        if Platform.isLinux:
            self._is_wayland = self._qt_application.platformName() == "wayland"
        else:
            self._is_wayland = False

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
                if not self._is_wayland:
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
