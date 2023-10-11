from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Property as QProperty
from PySide6.QtCore import QObject, QUrl
from PySide6.QtCore import Signal as QSignal
from PySide6.QtCore import Slot as QSlot
from PySide6.QtGui import QValidator

from bmnclient.coins.abstract.coin import Coin
from bmnclient.config import ApplicationConfig, KeyStoreConfig
from bmnclient.logger import Logger
from bmnclient.version import ProductPaths

from ..dialogs.key_store import RevealSeedPhraseDialog, TxApproveDialog
from .file import FileListModel, FileModel

if TYPE_CHECKING:
    from ....key_store import KeyStore
    from . import QmlApplication


class KeyStoreModel(QObject):
    keyStoreExported = QSignal()
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

    @QSlot(QUrl)
    def onExportBackupWallet(self, path: QUrl) -> None:
        locale_path = path.toLocalFile()

        if self._export(locale_path):
            self.keyStoreExported.emit()

    def _export(self, path: str) -> bool:
        path = Path(path)
        export_config = KeyStoreConfig(path)

        for key in KeyStoreConfig.Key:
            export_config.set(
                key,
                self._application.keyStore.config.get(key),
                save=False)
        return export_config.save()

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
    keyStoreImported = QSignal()

    def __init__(self, application: QmlApplication) -> None:
        super().__init__(application, application.walletsPath)

    def _filter(self, file: Path) -> bool:
        return (
            file.is_file()
            and file.suffix.lower() == ProductPaths.WALLET_SUFFIX.lower()
        )

    # TODO confirmation dialog
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

    @QSlot(QUrl)
    def onImportBackupWallet(self, path: QUrl) -> None:
        locale_path = path.toLocalFile()
        if self._import(locale_path):
            self._update()
            self.keyStoreImported.emit()

    def _update(self) -> None:
        super()._update()

        imported = self._application.config.get(
            ApplicationConfig.Key.IMPORTED_KEY_STORES,
            list,
            []
        )

        for path in imported:
            path = Path(path)
            if path in self._source_list or not self._filter(path):
                continue
            self.lock(self.Lock.INSERT, -1, 1)
            self._source_list.append(
                FileModel(self._application, path, logger=self._logger)
            )
            self._watcher.addPath(str(path))
            self.unlock()

    def _import(self, path: str) -> bool:
        path = Path(path)

        if not self._filter(path):
            return False

        imported = self._application.config.get(
            ApplicationConfig.Key.IMPORTED_KEY_STORES,
            list,
            []
        )

        if path in imported:
            return False

        imported.append(str(path))

        self._application.config.set(
            ApplicationConfig.Key.IMPORTED_KEY_STORES,
            imported,
            save=False
        )
        return self._application.config.save()
