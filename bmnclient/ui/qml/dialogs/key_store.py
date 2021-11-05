from __future__ import annotations

from enum import IntEnum
from random import randint
from typing import TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal

from . import AbstractDialog, AbstractMessageDialog, AbstractPasswordDialog
from ....key_store import GenerateSeedPhrase, KeyStoreError, RestoreSeedPhrase

if TYPE_CHECKING:
    from typing import Final, Optional
    from . import DialogManager


def createKeyStorePasswordDialog(manager: DialogManager) -> AbstractDialog:
    if manager.context.keyStore.native.isExists:
        return KeyStorePasswordDialog(manager)
    else:
        return KeyStoreNewPasswordDialog(manager)


class KeyStoreErrorDialog(AbstractMessageDialog):
    def __init__(
            self,
            manager: DialogManager,
            parent: AbstractDialog,
            *,
            text: str = QObject().tr("Unknown Key Store error.")):
        super().__init__(
            manager,
            parent,
            title=parent.title,  # noqa
            text=text)

    def onClosed(self) -> None:
        createKeyStorePasswordDialog(self._manager).open()


class KeyStoreNewPasswordDialog(AbstractDialog):
    _QML_NAME = "BKeyStoreNewPasswordDialog"

    def __init__(self, manager: DialogManager) -> None:
        super().__init__(manager)

    def onPasswordAccepted(self, password: str) -> None:
        if not self._manager.context.keyStore.native.create(password):
            KeyStoreErrorDialog(self._manager, self).open()
        else:
            createKeyStorePasswordDialog(self._manager).open()

    def onRejected(self) -> None:
        self._manager.context.exit(0)


class KeyStorePasswordDialog(AbstractDialog):
    _QML_NAME = "BKeyStorePasswordDialog"

    class ConfirmResetWalletDialog(AbstractMessageDialog):
        def __init__(
                self,
                manager: DialogManager,
                parent: KeyStorePasswordDialog):
            text = QObject().tr(
                "This will destroy all saved information and you can lose your "
                "money!"
                "\nPlease make sure you remember the Seed Phrase."
                "\n\nReset?")
            super().__init__(
                manager,
                parent,
                type_=AbstractMessageDialog.Type.AskYesNo,
                title=parent.title,  # noqa
                text=text)

        def onAccepted(self) -> None:
            if not self._manager.context.keyStore.native.reset():
                KeyStoreErrorDialog(self._manager, self).open()
            else:
                createKeyStorePasswordDialog(self._manager).open()

        def onRejected(self) -> None:
            createKeyStorePasswordDialog(self._manager).open()

    def __init__(self, manager: DialogManager) -> None:
        super().__init__(manager)

    def onPasswordAccepted(self, password: str) -> None:
        result = self._manager.context.keyStore.native.open(password)
        if result is KeyStoreError.ERROR_DERIVE_ROOT_HD_NODE:
            KeyStoreErrorDialog(
                self._manager,
                self,
                text=QObject().tr("Error derive Root HD Key.")).open()
        elif not result:
            KeyStoreErrorDialog(
                self._manager,
                self,
                text=QObject().tr("Wrong Key Store password.")).open()
        elif not self._manager.context.keyStore.native.hasSeed:
            NewSeedDialog(self._manager).open()

    def onResetWalletAccepted(self) -> None:
        self.ConfirmResetWalletDialog(self._manager, self).open()

    def onRejected(self) -> None:
        self._manager.context.exit(0)


class NewSeedDialog(AbstractDialog):
    _QML_NAME = "BNewSeedDialog"

    def __init__(self, manager: DialogManager) -> None:
        super().__init__(manager)

    def onGenerateAccepted(self) -> None:
        GenerateSeedPhraseDialog(self._manager, None).open()

    def onRestoreAccepted(self) -> None:
        RestoreSeedPhraseDialog(self._manager).open()

    def onRestoreBackupAccepted(self) -> None:
        raise NotImplementedError

    def onRejected(self) -> None:
        self._manager.context.exit(0)


class InvalidSeedPhraseDialog(AbstractMessageDialog):
    def __init__(
            self,
            manager: DialogManager,
            parent: ValidateSeedPhraseDialog,
            generator: Optional[GenerateSeedPhrase] = None):
        super().__init__(
            manager,
            parent,
            title=parent.title,  # noqa
            text=QObject().tr("Wrong Seed Phrase."))
        self._generator = generator

    def onClosed(self) -> None:
        if self._generator is not None:
            dialog = self._parent.__class__(self._manager, self._generator)
        else:
            dialog = self._parent.__class__(self._manager)
        dialog.open()


class AbstractSeedPhraseDialog(AbstractDialog):
    _QML_NAME = "BSeedPhraseDialog"
    _textChanged = QSignal()
    _isValidChanged = QSignal()

    class Type(IntEnum):
        Generate: Final = 0
        Validate: Final = 1
        Restore: Final = 2
        Reveal: Final = 3

    def __init__(self, manager: DialogManager) -> None:
        super().__init__(manager)
        self.__text = ""
        self.__is_valid = False

    @QProperty(str, notify=_textChanged)
    def text(self) -> str:
        return self.__text

    @text.setter
    def _setText(self, value: str) -> None:
        if self.__text != value:
            self.__text = value
            # noinspection PyUnresolvedReferences
            self._textChanged.emit()

    @QProperty(bool, notify=_isValidChanged)
    def isValid(self) -> bool:
        return self.__is_valid

    @isValid.setter
    def _setIsValid(self, value: bool) -> None:
        if self.__is_valid != value:
            self.__is_valid = value
            # noinspection PyUnresolvedReferences
            self._isValidChanged.emit()


class GenerateSeedPhraseDialog(AbstractSeedPhraseDialog):
    def __init__(
            self,
            manager: DialogManager,
            generator: Optional[GenerateSeedPhrase]) -> None:
        super().__init__(manager)
        self._qml_properties["type"] = self.Type.Generate.value
        if self._manager.context.debug.isEnabled:
            self._qml_properties["readOnly"] = False
        else:
            self._qml_properties["readOnly"] = True

        self._child_dialog: Optional[SeedSaltDialog] = None

        if generator is None:
            self._generator = GenerateSeedPhrase(
                self._manager.context.keyStore.native)
        else:
            self._generator = generator
        if self._generator.inProgress:
            self._setText(self._generator.update(None))
            self._setIsValid(True)

    @property
    def generator(self) -> GenerateSeedPhrase:
        return self._generator

    def _openSaltDialog(self) -> None:
        self._child_dialog = SeedSaltDialog(self._manager, self)
        self._child_dialog.open()

    def onOpened(self) -> None:
        if not self._generator.inProgress:
            self._openSaltDialog()

    def onReset(self) -> None:
        self._setText("")
        self._openSaltDialog()

    def onAccepted(self) -> None:
        ValidateSeedPhraseDialog(self._manager, self._generator).open()

    def onRejected(self) -> None:
        if self._child_dialog is not None:
            self._child_dialog.close.emit()
        NewSeedDialog(self._manager).open()


class ValidateSeedPhraseDialog(AbstractSeedPhraseDialog):
    def __init__(
            self,
            manager: DialogManager,
            generator: GenerateSeedPhrase) -> None:
        super().__init__(manager)
        self._qml_properties["type"] = self.Type.Validate.value
        self._qml_properties["readOnly"] = False
        self._generator = generator
        self._current_phrase = ""

    def onPhraseChanged(self, value: str) -> None:
        self._current_phrase = value
        self._setIsValid(self._generator.validate(self._current_phrase))

    def onAccepted(self) -> None:
        result = self._generator.finalize(self._current_phrase)
        if result is KeyStoreError.ERROR_DERIVE_ROOT_HD_NODE:
            KeyStoreErrorDialog(
                self._manager,
                self,
                text=QObject().tr("Error derive Root HD Key.")).open()
        elif not result:
            InvalidSeedPhraseDialog(
                self._manager,
                self,
                self._generator).open()

    def onRejected(self) -> None:
        GenerateSeedPhraseDialog(self._manager, self._generator).open()


class RestoreSeedPhraseDialog(AbstractSeedPhraseDialog):
    def __init__(self, manager: DialogManager) -> None:
        super().__init__(manager)
        self._qml_properties["type"] = self.Type.Restore.value
        self._qml_properties["readOnly"] = False
        self._generator = RestoreSeedPhrase(
                self._manager.context.keyStore.native)
        self._generator.prepare()
        self._current_phrase = ""

    def onPhraseChanged(self, value: str) -> None:
        self._current_phrase = value
        self._setIsValid(self._generator.validate(self._current_phrase))

    def onAccepted(self) -> None:
        result = self._generator.finalize(self._current_phrase)
        if result is KeyStoreError.ERROR_DERIVE_ROOT_HD_NODE:
            KeyStoreErrorDialog(
                self._manager,
                self,
                text=QObject().tr("Error derive Root HD Key.")).open()
        if not result:
            InvalidSeedPhraseDialog(self._manager, self).open()

    def onRejected(self) -> None:
        NewSeedDialog(self._manager).open()


class RevealSeedPhraseDialog(AbstractSeedPhraseDialog):
    class ErrorDialog(AbstractMessageDialog):
        def __init__(
                self,
                manager: DialogManager,
                parent: RevealSeedPhraseDialog,
                *,
                text: str):
            super().__init__(
                manager,
                parent,
                title=parent.title,  # noqa
                text=text)

        def onClosed(self) -> None:
            self._parent.PasswordDialog(self._manager, self._parent).open()

    class PasswordDialog(AbstractPasswordDialog):
        def __init__(
                self,
                manager: DialogManager,
                parent: RevealSeedPhraseDialog) -> None:
            super().__init__(
                manager,
                parent,
                title=parent.title) # noqa

        def onPasswordAccepted(self, password: str) -> None:
            result = self._manager.context.keyStore.native.revealSeedPhrase(
                password)
            if isinstance(result, str):
                self._parent.text = result
                return
            if result == KeyStoreError.ERROR_INVALID_PASSWORD:
                # noinspection PyTypeChecker
                text = self.tr("Wrong Key Store password.")
            elif result == KeyStoreError.ERROR_SEED_NOT_FOUND:
                # noinspection PyTypeChecker
                text = self.tr("Seed Phrase not found.")
            else:
                # noinspection PyTypeChecker
                text = self.tr("Unknown Key Store error.")
            self._parent.ErrorDialog(
                self._manager,
                self._parent,
                text=text).open()

        def onRejected(self) -> None:
            self._parent.close.emit()

    def __init__(self, manager: DialogManager) -> None:
        super().__init__(manager)
        self._qml_properties["type"] = self.Type.Reveal.value
        if self._manager.context.debug.isEnabled:
            self._qml_properties["readOnly"] = False
        else:
            self._qml_properties["readOnly"] = True

    def onOpened(self) -> None:
        self.PasswordDialog(self._manager, self).open()


class SeedSaltDialog(AbstractDialog):
    _QML_NAME = "BSeedSaltDialog"

    def __init__(
            self,
            manager: DialogManager,
            parent: GenerateSeedPhraseDialog) -> None:
        super().__init__(
            manager,
            parent,
            title=parent.title)  # noqa
        self._qml_properties["stepCount"] = 500 + randint(1, 501)

    def onAboutToShow(self) -> None:
        self._parent.text = self._parent.generator.prepare()

    def onUpdateSalt(self, value: str) -> None:
        self._parent.text = self._parent.generator.update(value)

    def onAccepted(self) -> None:
        self._parent.isValid = True
        self._parent.forceActiveFocus.emit()

    def onRejected(self) -> None:
        self._parent.reject.emit()
