import unittest
import logging
import PySide2.QtCore as qt_core
from client.ui.gui import settings_manager
# from client.wallet import language
log = logging.getLogger(__name__)


class TestLanguage(unittest.TestCase):

    def test_loading(self):
        app = qt_core.QCoreApplication()
        sett = settings_manager.SettingsManager(None)
        for lang in sett.languageModel:
            self.assertTrue(app.installTranslator(
                lang.py_translator), f"==> PY {lang}")
            self.assertTrue(app.installTranslator(
                lang.qml_translator), f"==> QML {lang}")
