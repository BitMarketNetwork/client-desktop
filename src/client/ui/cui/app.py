import sys
import logging
import PySide2.QtCore    as qt_core
log = logging.getLogger(__name__)

class ConsoleApp(qt_core.QCoreApplication):

    def __init__(self):
        super().__init__(sys.argv)