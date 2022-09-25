from __future__ import annotations
from enum import auto
import os, re

from typing import TYPE_CHECKING, Final
from .list import AbstractListModel, RoleEnum

from PySide6.QtCore import \
    QObject, \
    QFileInfo, \
    Slot as QSlot

from ..dialogs.key_store import RevealSeedPhraseDialog, TxApproveDialog
from ....coins.abstract.coin import Coin

if TYPE_CHECKING:
    from . import QmlApplication
    from ....key_store import KeyStore


class ConfigFolderListModel(AbstractListModel):
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
        super().__init__(
            application,
            [self._application.configPath/x for x in os.listdir(self._application.configPath)
            if re.match("[^\\s]+(.*?)\\.(json|JSON)$", x)])


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
