from __future__ import annotations
from enum import auto
import os, re

from typing import TYPE_CHECKING, Final, List
from .list import AbstractListModel, RoleEnum

from PySide6.QtCore import \
    QObject, \
    QFileInfo, \
    QFileSystemWatcher, \
    Signal as QSignal, \
    Property as QProperty, \
    Slot as QSlot

from ..dialogs.key_store import RevealSeedPhraseDialog, TxApproveDialog
from ....coins.abstract.coin import Coin

if TYPE_CHECKING:
    from . import QmlApplication
    from ....key_store import KeyStore


class ConfigFolderListModel(AbstractListModel):
    _countChanged = QSignal()

    class Role(RoleEnum):
        FILE_NAME: Final = auto()
        FILE_PATH: Final = auto()
        FILE_MODIFED: Final = auto()

    _ROLE_MAP: Final = {
        Role.FILE_NAME: (
            b"fileName",
            lambda c: QFileInfo(c).fileName()),
        Role.FILE_PATH: (
            b"filePath",
            lambda c: QFileInfo(c).filePath()),
        Role.FILE_MODIFED: (
            b"fileModified",
            lambda c: QFileInfo(c).lastModified())
    }

    def __init__(
            self,
            application: QmlApplication) -> None:
        self._application = application
        files = self._getConfigFolderFiles()

        super().__init__(application, files)

        self._folder_watcher = QFileSystemWatcher(self)
        if files:
            self._folder_watcher.addPaths(files)
            self._folder_watcher.fileChanged.connect(self.onFilechanged)
        self._count = self.rowCount()

    @QProperty(int, notify=_countChanged)
    def count(self) -> int:
        return self._count

    @QSlot(str)
    def onRemoveAccepted(self, path: str) -> None:
        if os.path.isfile(path):
            os.remove(path)

    @QSlot(str)
    def onFilechanged(self, path: str) -> None:
        if not os.path.isfile(path):
            self.lock(self.lockRemoveRows(self._source_list.index(path), 1))
            self.unlock()
            self._count = self.rowCount()
            self._countChanged.emit()

    def _getConfigFolderFiles(self) -> List[str]:
        return [str(self._application.configPath/x) for x in os.listdir(self._application.configPath)
            if re.match("[^\\s]+(.*?)\\.(json|JSON)$", x)]


class KeyStoreModel(QObject):
    def __init__(self, application: QmlApplication):
        super().__init__()
        self._application = application

    @property
    def native(self) -> KeyStore:
        return self._application.keyStore

    @QSlot()
    def onRevealSeedPhrase(self) -> None:
        # noinspection PyTypeChecker
        RevealSeedPhraseDialog(
            self._application.qmlContext.dialogManager).open()

    @QSlot(QObject)
    def onPrepareTransaction(self, coin: Coin) -> None:
        TxApproveDialog(
            self._application.qmlContext.dialogManager, coin).open()
