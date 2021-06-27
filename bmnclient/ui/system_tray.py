from __future__ import annotations

from enum import Enum
from os import getenv
from typing import TYPE_CHECKING

from PySide2.QtCore import QObject
from PySide2.QtWidgets import QMenu, QSystemTrayIcon

from ..logger import Logger
from ..os_environment import Platform
from ..version import Timer

if TYPE_CHECKING:
    from .gui import GuiApplication


class SystemTrayIcon(QObject):
    class MessageIcon(Enum):
        NONE = QSystemTrayIcon.MessageIcon.NoIcon
        INFORMATION = QSystemTrayIcon.MessageIcon.Information
        WARNING = QSystemTrayIcon.MessageIcon.Warning
        ERROR = QSystemTrayIcon.MessageIcon.Critical

    def __init__(self, application: GuiApplication) -> None:
        super().__init__()
        self._application = application
        self._logger = Logger.classLogger(self.__class__)
        self._enable_message_icon = True

        if not QSystemTrayIcon.isSystemTrayAvailable():
            self._logger.warning("System tray is not available.")
        if not QSystemTrayIcon.supportsMessages():
            self._logger.warning("System tray don't support balloon messages.")

        if Platform.isLinux:
            for v in getenv("XDG_CURRENT_DESKTOP", "").split(":"):
                if v.lower() == "xfce":
                    self._logger.warning(
                        "System tray with Xfce+Qt message icon bug.")
                    self._enable_message_icon = False
                    break

        self._createMenu()
        self._createIcon()

    def _createMenu(self) -> None:
        self._menu = QMenu(self._application.title)

        # noinspection PyTypeChecker
        self._menu.setDefaultAction(self._menu.addAction(
            self.tr("&Show/Hide main window"),
            self._onToggleMainWindow))
        self._menu.addSeparator()
        # noinspection PyTypeChecker
        self._menu.addAction(
            self.tr("&Quit"),
            self._onQuit)

    def _createIcon(self) -> None:
        self._icon = QSystemTrayIcon()
        self._icon.setIcon(self._application.icon)
        self._icon.setToolTip(self._application.title)
        # noinspection PyUnresolvedReferences
        self._icon.activated.connect(self._onIconActivated)
        # noinspection PyUnresolvedReferences
        self._icon.messageClicked.connect(self._onMessageClicked)
        self._icon.setContextMenu(self._menu)
        self.show()

    def _onToggleMainWindow(self) -> None:
        self._application.show(not self._application.isVisible)

    def _onActivateMainWindow(self) -> None:
        self._application.show(True)

    def _onQuit(self) -> None:
        self._application.setExitEvent(0)

    def _onIconActivated(
            self,
            reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._onToggleMainWindow()

    def _onMessageClicked(self) -> None:
        self._onActivateMainWindow()

    def show(self, show: bool = True) -> None:
        self._icon.setVisible(show)

    def showMessage(
            self,
            title: str,
            text: str,
            icon: MessageIcon = MessageIcon.INFORMATION,
            timeout: int = Timer.UI_MESSAGE_TIMEOUT) -> None:
        if not self._enable_message_icon:
            icon = self.MessageIcon.NONE

        self._logger.debug("Message (%s):\n\t%s\n\t%s", str(icon), title, text)
        self._icon.showMessage(
            title,
            text,
            icon.value,
            timeout)
