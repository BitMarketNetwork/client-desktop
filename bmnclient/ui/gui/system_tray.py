# JOK+
from enum import IntEnum

from PySide2 import QtCore
from PySide2.QtWidgets import QSystemTrayIcon, QMenu

from bmnclient.logger import getClassLogger
from bmnclient.ui import CoreApplication


class MessageIcon(IntEnum):
    NONE = 0
    INFORMATION = 1
    WARNING = 2
    CRITICAL = 3


class SystemTrayIcon(QtCore.QObject):
    quit = QtCore.Signal()
    showMainWindow = QtCore.Signal()
    hideMainWindow = QtCore.Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self._logger = getClassLogger(__name__, self.__class__)

        if not QSystemTrayIcon.isSystemTrayAvailable() or True:
            self._logger.warning("System tray is not available.")
        if not QSystemTrayIcon.supportsMessages():
            self._logger.warning("System tray don't support balloon messages.")

        self._menu = QMenu(CoreApplication.instance().title)
        self._fillMenu()

        self._tray_icon = QSystemTrayIcon(self)
        self._tray_icon.setIcon(CoreApplication.instance().icon)
        self._tray_icon.setToolTip(CoreApplication.instance().title)
        self._tray_icon.activated.connect(self._onActivated)
        self._tray_icon.messageClicked.connect(self._onMessageClicked)
        self._tray_icon.setContextMenu(self._menu)

    def _fillMenu(self) -> None:
        self._show_action = self._menu.addAction(
            self.tr("Show"),
            self.showMainWindow.emit)
        self._hide_action = self._menu.addAction(
            self.tr("Hide"),
            self.hideMainWindow.emit)

        self._menu.addSeparator()

        self._menu.addAction(
            self.tr("Quit"),
            self.quit.emit)

    @QtCore.Slot()
    def _onActivated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.showMainWindow.emit()

    @QtCore.Slot()
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
            QtCore.QCoreApplication.instance().applicationName(),
            message,
            icon_map[icon],
            timeout)
