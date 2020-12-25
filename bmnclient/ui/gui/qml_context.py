from PySide2 import QtCore

from bmnclient.debug_manager import DebugManager
from bmnclient.wallet.master_key import KeyManager
from .coin_manager import CoinManager
from .receive_manager import ReceiveManager
from .settings_manager import SettingsManager
from .ui_manager import UIManager
import bmnclient.command_line


class BackendContext(QtCore.QObject):
    def __init__(self, owner, parent=None) -> None:
        super().__init__(parent=parent)
        self._owner = owner
        self.__class__.__instance = self

    @QtCore.Property(CoinManager, constant=True)
    def coinManager(self) -> CoinManager:
        return self._owner._coin_manager

    @QtCore.Property(UIManager, constant=True)
    def uiManager(self) -> UIManager:
        return self._owner._ui_manager

    @QtCore.Property(DebugManager, constant=True)
    def debugManager(self) -> DebugManager:
        return self.parent().debug_man

    @QtCore.Property(KeyManager, constant=True)
    def keyManager(self) -> KeyManager:
        return self.parent().key_man

    @QtCore.Property(SettingsManager, constant=True)
    def settingsManager(self) -> SettingsManager:
        return self._owner._settings_manager

    @QtCore.Property(ReceiveManager, constant=True)
    def receiveManager(self) -> ReceiveManager:
        return self._owner._receive_manager

    @QtCore.Property(bool, constant=True)
    def debugMode(self) -> bool:
        return bmnclient.command_line.debug_mode()

    ############################################################################
    # TODO kill
    ############################################################################

    __instance = None

    @property
    def gcd(self):
        return self.parent()

    @classmethod
    def get_instance(cls):
        return cls.__instance
