from __future__ import annotations

from . import AbstractDialog
from .key_store import createKeyStorePasswordDialog


class BAlphaDialog(AbstractDialog):
    def onAccepted(self) -> None:
        createKeyStorePasswordDialog(self._manager).open()

    def onRejected(self) -> None:
        self._manager.context.exit(0)


class BQuitDialog(AbstractDialog):
    def onAccepted(self) -> None:
        self._manager.context.exit(0)
