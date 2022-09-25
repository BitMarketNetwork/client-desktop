from __future__ import annotations

from typing import TYPE_CHECKING

from . import AbstractDialog
from .key_store import selectKeyStoreDialog

if TYPE_CHECKING:
    from . import DialogManager


class AlphaDialog(AbstractDialog):
    _QML_NAME = "BAlphaDialog"

    def __init__(self, manager: DialogManager) -> None:
        super().__init__(manager)

    def onAccepted(self) -> None:
        selectKeyStoreDialog(self._manager).open()

    def onRejected(self) -> None:
        self._manager.context.exit(0)


class QuitDialog(AbstractDialog):
    _QML_NAME = "BQuitDialog"

    def __init__(self, manager: DialogManager) -> None:
        super().__init__(manager)

    def onAccepted(self) -> None:
        self._manager.context.exit(0)
