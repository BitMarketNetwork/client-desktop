import logging
from typing import Any
import PySide2.QtCore as qt_core

log = logging.getLogger(__name__)

CONFIG_FILENAME = "config.ini"


class AppBase:
    debug_mode = False
    
    def read_config(self) -> bool:
        # self._config = qt_core.QSettings(CONFIG_FILENAME, qt_core.QSettings.IniFormat,parent=self)
        # AppBase.debug_mode = self._get_property("debug_mode", False) == "true"
        # if AppBase.debug_mode:
        #     log.warning("DEBUG MODE")
        return True

    def _get_property(self, name: str, default: Any)-> Any:
        if not self._config.contains(name):
            self._config.setValue(name, default)
            return str(default).lower()
        return self._config.value(name)

