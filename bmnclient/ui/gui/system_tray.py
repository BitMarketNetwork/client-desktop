import logging
import enum

from PySide2 import QtCore as qt_core
from PySide2 import QtGui as qt_gui
from PySide2 import QtWidgets as qt_widgets

import bmnclient.version
from ... import meta

log = logging.getLogger(__name__)


class Messagelevel(enum.IntEnum):
    none = 0
    info = enum.auto()
    warning = enum.auto()
    error = enum.auto()


assert Messagelevel.error == 3


class SystemTray(qt_core.QObject):
    quit = qt_core.Signal()

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.__tray = qt_widgets.QSystemTrayIcon(self)
        # TODO shared QIcon
        self.__tray.setIcon(qt_gui.QIcon(str(bmnclient.resources.ICON_FILE_PATH)))
        self.__make_menu()
        self.__tray.show()
        # assert self.__tray.available
        #
        assert self.__tray.supportsMessages()

    def __make_menu(self):
        menu = qt_widgets.QMenu()
        action = menu.addAction(
            qt_core.QCoreApplication.instance().applicationName())
        action.setDisabled(True)
        menu.addSeparator()
        self.__show_action = menu.addAction(self.tr("Show"))
        self.__show_action.triggered.connect(self.__show)
        self.__hide_action = menu.addAction(self.tr("Hide"))
        self.__hide_action.triggered.connect(self.__hide)
        menu.addSeparator()
        action = menu.addAction(self.tr("Close"))
        action.triggered.connect(self.quit)
        self.__tray.setContextMenu(menu)
        self.__tray.activated.connect(self.__reaction)
        self.__tray.messageClicked.connect(self.__baloon_click)

    def __show(self):
        self.parent().show.emit()

    def __hide(self):
        self.parent().hide.emit()

    def __reaction(self, reason):
        # log.warning(f"tray action: {reason}")
        # if reason == self.__tray.ActivationReason.DoubleClick:
        # if reason == self.__tray.ActivationReason.Context:
        if reason == self.__tray.ActivationReason.Trigger:
            self.__show()

    def __baloon_click(self):
        log.debug(f"baloon click")
        self.__show()


    def set_visible(self, on: bool):
        self.__show_action.setVisible(not on)
        self.__hide_action.setVisible(on)

    def notify(self, message: str, level: Messagelevel):
        title = qt_core.QCoreApplication.instance().applicationName()
        self.__tray.showMessage(
            title,
            message,
            qt_widgets.QSystemTrayIcon.MessageIcon(level),
            30000 + level * 10000)
        if meta.IS_OSX:
            import os
            os.system(
                f"""osascript -e 'display notification \"{message}\" with title \"{title}\"'""")
        log.debug(f"tray message: {message} level:{level}")
