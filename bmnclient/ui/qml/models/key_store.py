from __future__ import annotations
from enum import auto
import os

from typing import TYPE_CHECKING, Final, Optional
from .list import AbstractFolderListModel, RoleEnum
from ....os_environment import PlatformPaths

from PySide6.QtCore import \
    QObject, \
    QFileInfo, \
    Property as QProperty, \
    Slot as QSlot
from PySide6.QtGui import QValidator

from ..dialogs.key_store import RevealSeedPhraseDialog, TxApproveDialog
from ....coins.abstract.coin import Coin

if TYPE_CHECKING:
    from . import QmlApplication
    from ....key_store import KeyStore


class ConfigFolderListModel(AbstractFolderListModel):
    class Role(RoleEnum):
        FILE_NAME: Final = auto()
        FILE_PATH: Final = auto()
        FILE_MODIFED: Final = auto()

    _ROLE_MAP: Final = {
        Role.FILE_NAME: (
            b"fileName",
            lambda c: QFileInfo(c).baseName()),
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
        super().__init__(
            application,
            application.walletsPath,
            "[^\\s]+(.*?)\\.(json|JSON)$")

    @QSlot(str)
    def onRemoveAccepted(self, path: str) -> None:
        if os.path.isfile(path):
            os.remove(path)


class KeyStoreModel(QObject):
    class _KeyStoreNameValidator(QValidator):
        # Temporary
        def __init__(self, parent: Optional[QObject] = ...) -> None:
            super().__init__(parent)
            self._invalid_chars = PlatformPaths.invalidFileNameChars

        def validate(self, text: str, position: int) -> QValidator.State:
            if text.startswith(" "):
                return QValidator.Invalid
            if text:
                for ch in self._invalid_chars:
                    if ch in text:
                        return QValidator.Invalid
            return QValidator.Acceptable

    def __init__(self, application: QmlApplication):
        super().__init__()
        self._application = application
        self._name_validator = self._KeyStoreNameValidator(self)

    @property
    def native(self) -> KeyStore:
        return self._application.keyStore

    @QProperty(QObject, constant=True)
    def nameValidator(self) -> QValidator:
        return self._name_validator

    @QSlot()
    def onRevealSeedPhrase(self) -> None:
        # noinspection PyTypeChecker
        RevealSeedPhraseDialog(
            self._application.qmlContext.dialogManager).open()

    @QSlot(QObject)
    def onPrepareTransaction(self, coin: Coin) -> None:
        TxApproveDialog(
            self._application.qmlContext.dialogManager, coin).open()
