# JOK+
from __future__ import annotations

from PySide2 import QtCore
from PySide2 import QtGui

from bmnclient import version, resources
from bmnclient.logger import getClassLogger


class CoreApplication(QtCore.QObject):
    _instance = None

    def __init__(self, qt_class, argv) -> None:
        assert self.__class__._instance is None

        self._logger = getClassLogger(__name__, self.__class__)
        self._title = "{} {}".format(version.NAME, version.VERSION_STRING)
        self._icon = None
        self._language = None

        QtCore.QLocale.setDefault(QtCore.QLocale.c())

        qt_class.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
        qt_class.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
        qt_class.setAttribute(QtCore.Qt.AA_DisableShaderDiskCache)
        qt_class.setAttribute(QtCore.Qt.AA_DisableWindowContextHelpButton)

        qt_class.setApplicationName(version.NAME)
        qt_class.setApplicationVersion(version.VERSION_STRING)
        qt_class.setOrganizationName(version.MAINTAINER)
        qt_class.setOrganizationDomain(version.MAINTAINER_DOMAIN)

        self._qt_application = qt_class(argv)
        super().__init__()

        if issubclass(qt_class, QtGui.QGuiApplication):
            self._icon = QtGui.QIcon(str(resources.ICON_FILE_PATH))
            qt_class.setWindowIcon(self._icon)

        CoreApplication._instance = self

    def runEventLoop(self) -> int:
        # We recommend that you connect clean-up code to the aboutToQuit()
        # signal, instead of putting it in your application's main() function
        # because on some platforms the exec() call may not return.
        exit_code = self._qt_application.exec_()

        if exit_code == 0:
            self._logger.info(
                "%s terminated successfully.",
                version.NAME)
        else:
            self._logger.warning(
                "%s terminated with error.",
                version.NAME)
        return exit_code

    @property
    def title(self) -> str:
        return self._title

    @property
    def icon(self) -> QtGui.QIcon:
        return self._icon

    @classmethod
    def instance(cls) -> CoreApplication:
        return cls._instance
