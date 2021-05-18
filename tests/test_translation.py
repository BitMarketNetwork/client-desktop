import logging
from unittest import skip, TestCase

import PySide2.QtCore as qt_core

from bmnclient.ui.gui import settings_manager

log = logging.getLogger(__name__)


@skip
class TestLanguage(TestCase):
    def test_loading(self) -> None:
        app = qt_core.QCoreApplication()
        sett = settings_manager.SettingsManager(None)
        for lang in sett.languageModel:
            self.assertTrue(app.installTranslator(
                lang.py_translator), f"==> PY {lang}")
            self.assertTrue(app.installTranslator(
                lang.qml_translator), f"==> QML {lang}")
