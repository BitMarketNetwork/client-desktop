
import sys
import PySide2.QtCore as qt_core
import PySide2.QtGui as qt_qui
import PySide2.QtWidgets as qt_widgets
from ...config import version as e_config_version


class GuiApplication(qt_widgets.QApplication):

    def __init__(self, style: str = None):
        if style:
            sys.argv += ['--style', style]
        self.setAttribute(qt_core.Qt.AA_EnableHighDpiScaling)
        self.setAttribute(qt_core.Qt.AA_UseHighDpiPixmaps)
        super().__init__(sys.argv)
        self.setWindowIcon(qt_qui.QIcon( ":/qml/media/logo.ico"))
        self.setApplicationName(e_config_version.CLIENT_NAME)
        self.setApplicationVersion(
            ".".join(map(str, e_config_version.CLIENT_VERSION)))
        self.setOrganizationName(e_config_version.CLIENT_ORGANIZATION)
        self.setOrganizationDomain(e_config_version.CLIENT_ORGANIZATION_DOMAIN)