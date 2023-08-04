from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Property as QProperty
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal as QSignal
from PySide6.QtCore import Slot as QSlot
from PySide6.QtGui import QValidator

from bmnclient.coins.abstract.coin import Coin
from bmnclient.config import KeyStoreConfig
from bmnclient.logger import Logger
from bmnclient.version import ProductPaths

from ..dialogs.key_store import RevealSeedPhraseDialog, TxApproveDialog
from .file import FileListModel

if TYPE_CHECKING:
    from ....key_store import KeyStore
    from . import QmlApplication


class KeyStoreModel(QObject):
    class _KeyStoreNameValidator(QValidator):
        def validate(self, value: str, position: int) -> QValidator.State:
            if not value:
                return QValidator.State.Intermediate
            if not KeyStoreConfig.isValidName(value):
                return QValidator.State.Invalid
            return QValidator.State.Acceptable

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
        RevealSeedPhraseDialog(
            self._application.qmlContext.dialogManager
        ).open()

    @QSlot(QObject)
    def onPrepareTransaction(self, coin: Coin) -> None:
        TxApproveDialog(
            self._application.qmlContext.dialogManager, coin
        ).open()


class KeyStoreListModel(FileListModel):
    def __init__(self, application: QmlApplication) -> None:
        super().__init__(application, application.walletsPath)

    def _filter(self, file: Path) -> bool:
        return (
            file.is_file()
            and file.suffix.lower() == ProductPaths.WALLET_SUFFIX.lower()
        )

    @QSlot(str)
    def onRemoveAccepted(self, path: str) -> None:
        path = Path(path)
        if path not in self._source_list:  # advanced protection
            return
        try:
            path.unlink(missing_ok=True)
        except OSError as exp:
            self._logger.debug(
                "Failed to remove file '%s'. %s",
                path,
                Logger.osErrorString(exp),
            )
            # TODO: UI message
