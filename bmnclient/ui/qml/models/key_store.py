from __future__ import annotations

from typing import TYPE_CHECKING

from PySide2.QtCore import \
    QObject, \
    Slot as QSlot

from ..dialogs.key_store import RevealSeedPhraseDialog

if TYPE_CHECKING:
    from . import QmlApplication
    from ....key_store import KeyStore


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
