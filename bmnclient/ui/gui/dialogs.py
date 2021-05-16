# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import BackendContext


def _askKeyStorePassword(context: BackendContext) -> None:
    if context.keyStore.hasPassword:
        context.uiManager.openDialog(BKeyStorePasswordDialog)
    else:
        context.uiManager.openDialog(BKeyStoreNewPasswordDialog)


class Dialog:
    def __init__(self, context: BackendContext) -> None:
        self._context = context

    def onRejected(self) -> None:
        self._context.uiManager.exit(0)


class BAlphaDialog(Dialog):
    def onAccepted(self) -> None:
        _askKeyStorePassword(self._context)


class BKeyStoreNewPasswordDialog(Dialog):
    def onPasswordReady(self) -> None:
        _askKeyStorePassword(self._context)


class BKeyStorePasswordDialog(Dialog):
    def onResetWalletAccepted(self) -> None:
        _askKeyStorePassword(self._context)

    def onPasswordReady(self) -> None:
        if not self._context.keyStore.hasSeed:
            self._context.uiManager.openDialog(BNewSeedDialog)


class BNewSeedDialog(Dialog):
    pass
