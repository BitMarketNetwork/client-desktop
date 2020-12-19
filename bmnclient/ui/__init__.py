# JOK
from __future__ import annotations

import logging

import PySide2.QtCore as QtCore
import PySide2.QtGui as QtGui

import bmnclient.version

logger = logging.getLogger(__name__)


class ApplicationBase(QtCore.QObject):
    _instance = None

    def __init__(self, qt_class, argv) -> None:
        assert self.__class__._instance is None

        QtCore.QLocale.setDefault(QtCore.QLocale.c())

        qt_class.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
        qt_class.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
        qt_class.setAttribute(QtCore.Qt.AA_DisableShaderDiskCache)
        qt_class.setAttribute(QtCore.Qt.AA_DisableWindowContextHelpButton)

        qt_class.setApplicationName(
            bmnclient.version.NAME)
        qt_class.setApplicationVersion(
            ".".join(map(str, bmnclient.version.VERSION)))
        qt_class.setOrganizationName(
            bmnclient.version.MAINTAINER)
        qt_class.setOrganizationDomain(
            bmnclient.version.MAINTAINER_DOMAIN)

        self._qt_application = qt_class(argv)
        super().__init__()

        self._application_icon = None
        self._application_language = None

        if issubclass(qt_class, QtGui.QGuiApplication):
            self._application_icon = QtGui.QIcon(
                str(bmnclient.resources.ICON_FILE_PATH))
            qt_class.setWindowIcon(self._application_icon)

        self.__class__._instance = self

    def runEventLoop(self) -> int:
        # We recommend that you connect clean-up code to the aboutToQuit()
        # signal, instead of putting it in your application's main() function
        # because on some platforms the exec() call may not return.
        exit_code = self._qt_application.exec_()

        if exit_code == 0:
            logger.info(
                "%s terminated successfully.",
                bmnclient.version.NAME)
        else:
            logger.warning(
                "%s terminated with error.",
                bmnclient.version.NAME)
        return exit_code

    @property
    def windowIcon(self) -> QtGui.QIcon:
        return self._application_icon

    @classmethod
    def instance(cls) -> ApplicationBase:
        return cls._instance
