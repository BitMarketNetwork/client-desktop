from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from PySide2.QtCore import \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot

from . import AbstractDialog, AbstractMessageDialog
from ....logger import Logger
from ....utils.class_property import classproperty

if TYPE_CHECKING:
    from typing import Dict, Final, List, Optional, Type, Union
    from . import DialogManager
    from .. import QmlContext


def createKeyStorePasswordDialog(manager: DialogManager) -> AbstractDialog:
    if manager.context.keyStore.isExists:
        return BKeyStorePasswordDialog(manager)
    else:
        return BKeyStoreNewPasswordDialog(manager)


class InvalidPasswordDialog(AbstractMessageDialog):
    def __init__(self, manager: DialogManager):
        super().__init__(
            manager,
            text=QObject().tr("Wrong key store password."))

    def onClosed(self) -> None:
        createKeyStorePasswordDialog(self._manager).open()


class ConfirmResetWalletDialog(AbstractMessageDialog):
    def __init__(self, manager: DialogManager):
        text = QObject().tr(
            "This will destroy all saved information and you can lose your "
            "money!"
            "\nPlease make sure you remember the seed phrase."
            "\n\nReset?")
        super().__init__(
            manager,
            type_=AbstractMessageDialog.Type.AskYesNo,
            text=text)

    def onAccepted(self) -> None:
        self._manager.context.keyStore.reset()  # TODO if failed
        createKeyStorePasswordDialog(self._manager).open()

    def onRejected(self) -> None:
        createKeyStorePasswordDialog(self._manager).open()


class BKeyStoreNewPasswordDialog(AbstractDialog):
    def onPasswordAccepted(self, password: str) -> None:
        self._manager.context.keyStore.create(password)  # TODO if failed
        createKeyStorePasswordDialog(self._manager).open()

    def onRejected(self) -> None:
        self._manager.context.exit(0)


class BKeyStorePasswordDialog(AbstractDialog):
    def onPasswordAccepted(self, password: str) -> None:
        if not self._manager.context.keyStore.open(password):
            InvalidPasswordDialog(self._manager).open()
        elif not self._manager.context.keyStore.hasSeed:
            BNewSeedDialog(self._manager).open()

    def onResetWalletAccepted(self) -> None:
        ConfirmResetWalletDialog(self._manager).open()

    def onRejected(self) -> None:
        self._manager.context.exit(0)


class BNewSeedDialog(AbstractDialog):
    def onGenerateAccepted(self) -> None:
        GenerateSeedPhraseDialog(self._manager).open()

    def onRestoreAccepted(self) -> None:
        RestoreSeedPhraseDialog(self._manager).open()

    def onRestoreBackupAccepted(self) -> None:
        raise NotImplementedError

    def onRejected(self) -> None:
        self._manager.context.exit(0)

