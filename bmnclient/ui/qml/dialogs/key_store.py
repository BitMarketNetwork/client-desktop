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


class AbstractSeedPhraseDialog(AbstractDialog):
    _QML_NAME = "BSeedPhraseDialog"
    _textChanged = QSignal()

    class Type(IntEnum):
        Generate: Final = 0
        Validate: Final = 1
        Restore: Final = 2
        Reveal: Final = 3

    def __init__(self, manager: DialogManager) -> None:
        super().__init__(manager)
        self._text = ""

    @QProperty(str, notify=_textChanged)
    def text(self) -> str:
        return self._text

    @text.setter
    def _setText(self, value: str) -> None:
        if self._text != value:
            self._text = value
            # noinspection PyUnresolvedReferences
            self._textChanged.emit()


class GenerateSeedPhraseDialog(AbstractSeedPhraseDialog):
    def __init__(self, manager: DialogManager) -> None:
        super().__init__(manager)
        self._qml_properties["type"] = self.Type.Generate.value
        self._qml_properties["enableAccept"] = True
        self._child_dialog: Optional[BSeedSaltDialog] = None

        if not self._manager.context.debug.isEnabled:
            self._qml_properties["readOnly"] = True

    def _openSaltDialog(self) -> None:
        self._child_dialog = BSeedSaltDialog(self._manager, self)
        self._child_dialog.open()

    def onOpened(self) -> None:
        self._openSaltDialog()

    def onReset(self) -> None:
        self._setText("")
        self._openSaltDialog()

    def onAccepted(self) -> None:
        ValidateSeedPhraseDialog(self._mamager).open()

    def onRejected(self) -> None:
        if self._child_dialog is not None:
            self._child_dialog.close.emit()
        BNewSeedDialog(self._manager).open()


class BSeedSaltDialog(AbstractDialog):
    def __init__(
            self,
            manager: DialogManager,
            parent: GenerateSeedPhraseDialog) -> None:
        super().__init__(manager)
        self._qml_properties["stepCount"] = 500 + randint(1, 501)
        self._parent = parent
        self._generator = GenerateSeedPhrase(
            self._manager.context.keyStore.native)

    def onAboutToShow(self) -> None:
        self._parent.text = self._generator.prepare()

    def onUpdateSalt(self, value: str) -> None:
        self._parent.text = self._generator.update(value)

    def onAccepted(self) -> None:
        self._parent.forceActiveFocus.emit()

    def onRejected(self) -> None:
        self._parent.reject.emit()


