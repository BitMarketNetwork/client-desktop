from __future__ import annotations

from enum import IntEnum
from random import randint
from typing import TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal

from . import AbstractDialog, AbstractMessageDialog, AbstractPasswordDialog
from ....key_store import GenerateSeedPhrase, RestoreSeedPhrase

if TYPE_CHECKING:
    from typing import Final, Optional
    from . import DialogManager


def createKeyStorePasswordDialog(manager: DialogManager) -> AbstractDialog:
    if manager.context.keyStore.isExists:
        return BKeyStorePasswordDialog(manager)
    else:
        return BKeyStoreNewPasswordDialog(manager)


class BKeyStoreNewPasswordDialog(AbstractDialog):
    def onPasswordAccepted(self, password: str) -> None:
        self._manager.context.keyStore.create(password)  # TODO if failed
        createKeyStorePasswordDialog(self._manager).open()

    def onRejected(self) -> None:
        self._manager.context.exit(0)


class BKeyStorePasswordDialog(AbstractDialog):
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

    class InvalidPasswordDialog(AbstractMessageDialog):
        def __init__(self, manager: DialogManager):
            super().__init__(
                manager,
                text=QObject().tr("Wrong key store password."))

        def onClosed(self) -> None:
            createKeyStorePasswordDialog(self._manager).open()

    def onPasswordAccepted(self, password: str) -> None:
        if not self._manager.context.keyStore.open(password):
            self.InvalidPasswordDialog(self._manager).open()
        elif not self._manager.context.keyStore.hasSeed:
            BNewSeedDialog(self._manager).open()

    def onResetWalletAccepted(self) -> None:
        self.ConfirmResetWalletDialog(self._manager).open()

    def onRejected(self) -> None:
        self._manager.context.exit(0)


class BNewSeedDialog(AbstractDialog):
    def onGenerateAccepted(self) -> None:
        GenerateSeedPhraseDialog(self._manager, None).open()

    def onRestoreAccepted(self) -> None:
        RestoreSeedPhraseDialog(self._manager).open()

    def onRestoreBackupAccepted(self) -> None:
        raise NotImplementedError

    def onRejected(self) -> None:
        self._manager.context.exit(0)


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
        if not self._manager.context.debug.isEnabled:
            self._qml_properties["readOnly"] = True

        self._child_dialog: Optional[BSeedSaltDialog] = None

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
        self._child_dialog = BSeedSaltDialog(self._manager, self)
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
        BNewSeedDialog(self._manager).open()


class ValidateSeedPhraseDialog(AbstractSeedPhraseDialog):
    class InvalidSeedPhraseDialog(AbstractMessageDialog):
        def __init__(
                self,
                manager: DialogManager,
                generator: GenerateSeedPhrase):
            super().__init__(
                manager,
                text=QObject().tr("Wrong seed phrase."))
            self._generator = generator

        def onClosed(self) -> None:
            ValidateSeedPhraseDialog(self._manager, self._generator).open()

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
        if not self._generator.finalize(self._current_phrase):
            self.InvalidSeedPhraseDialog(self._manager, self._generator).open()

    def onRejected(self) -> None:
        GenerateSeedPhraseDialog(self._manager, self._generator).open()


class RestoreSeedPhraseDialog(AbstractSeedPhraseDialog):
    class InvalidSeedPhraseDialog(AbstractMessageDialog):
        def __init__(self, manager: DialogManager):
            super().__init__(
                manager,
                text=QObject().tr("Wrong seed phrase."))

        def onClosed(self) -> None:
            RestoreSeedPhraseDialog(self._manager).open()

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
        if not self._generator.finalize(self._current_phrase):
            self.InvalidSeedPhraseDialog(self._manager).open()

    def onRejected(self) -> None:
        BNewSeedDialog(self._manager).open()


class BSeedSaltDialog(AbstractDialog):
    def __init__(
            self,
            manager: DialogManager,
            parent: GenerateSeedPhraseDialog) -> None:
        super().__init__(manager)
        self._qml_properties["stepCount"] = 500 + randint(1, 501)
        self._parent = parent

    def onAboutToShow(self) -> None:
        self._parent.text = self._parent.generator.prepare()

    def onUpdateSalt(self, value: str) -> None:
        self._parent.text = self._parent.generator.update(value)

    def onAccepted(self) -> None:
        self._parent.isValid = True
        self._parent.forceActiveFocus.emit()

    def onRejected(self) -> None:
        self._parent.reject.emit()


