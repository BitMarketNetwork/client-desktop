# JOK+
from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from PySide2.QtCore import \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot
from PySide2.QtWidgets import QMenu, QSystemTrayIcon

from ...logger import Logger

if TYPE_CHECKING:
    from . import GuiApplication


class MessageIcon(IntEnum):
    NONE = 0
    INFORMATION = 1
    WARNING = 2
    CRITICAL = 3


class SystemTrayIcon(QObject):
    exit = QSignal()
    showMainWindow = QSignal()
    hideMainWindow = QSignal()

    def __init__(self, application: GuiApplication) -> None:
        super().__init__()
        self._application = application
        self._logger = Logger.getClassLogger(__name__, self.__class__)

        if not QSystemTrayIcon.isSystemTrayAvailable():
            self._logger.warning("System tray is not available.")
        if not QSystemTrayIcon.supportsMessages():
            self._logger.warning("System tray don't support balloon messages.")

        self._menu = QMenu(self._application.title)
        self._fillMenu()

        self._tray_icon = QSystemTrayIcon(self)
        self._tray_icon.setIcon(self._application.icon)
        self._tray_icon.setToolTip(self._application.title)
        self._tray_icon.activated.connect(self._onActivated)
        self._tray_icon.messageClicked.connect(self._onMessageClicked)
        self._tray_icon.setContextMenu(self._menu)

    def _fillMenu(self) -> None:
        # noinspection PyTypeChecker
        self._show_action = self._menu.addAction(
            self.tr("Show"),
            self.showMainWindow.emit)
        # noinspection PyTypeChecker
        self._hide_action = self._menu.addAction(
            self.tr("Hide"),
            self.hideMainWindow.emit)

        self._menu.addSeparator()

        # noinspection PyTypeChecker
        self._menu.addAction(
            self.tr("Quit"),
            self.exit.emit)

    @QSlot()
    def _onActivated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.showMainWindow.emit()

    @QSlot()
    def _onMessageClicked(self) -> None:
        self.showMainWindow.emit()

    def setMainWindowVisibleState(self, visible: bool) -> None:
        self._show_action.setVisible(not visible)
        self._hide_action.setVisible(visible)

    def show(self, show: bool = True) -> None:
        self._tray_icon.setVisible(show)

    def showMessage(
            self,
            message: str,
            icon: int = MessageIcon.INFORMATION,
            timeout: int = 10 * 1000) -> None:
        icon_map = (
            QSystemTrayIcon.MessageIcon.NoIcon,
            QSystemTrayIcon.MessageIcon.Information,
            QSystemTrayIcon.MessageIcon.Warning,
            QSystemTrayIcon.MessageIcon.Critical
        )
        assert len(MessageIcon) == len(icon_map)

        self._logger.debug("Message %i: %s.", icon, message)
        self._tray_icon.showMessage(
            self._application.title,
            message,
            # TODO this icon replace tray icon icon_map[icon],
            QSystemTrayIcon.MessageIcon.NoIcon,
            timeout)
