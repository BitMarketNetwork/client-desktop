from __future__ import annotations

from enum import IntEnum
from pathlib import Path
from random import randint
from typing import TYPE_CHECKING

from PySide6.QtCore import (
    Property as QProperty,
    QObject,
    Signal as QSignal
)

from . import AbstractDialog, AbstractMessageDialog, AbstractPasswordDialog
from ....coins.abstract.coin import Coin
from ....key_store import GenerateSeedPhrase, KeyStoreError, RestoreSeedPhrase

if TYPE_CHECKING:
    from typing import Final, Optional
    from . import DialogManager

def selectKeyStoreDialog(manager: DialogManager) -> AbstractDialog:
    return KeyStoreSelectDialog(manager)


class ConfirmPasswordDialog(AbstractPasswordDialog):
    _QML_NAME = "BKeyStoreConfirmPasswordDialog"

    def onPasswordAccepted(self, password: str) -> None:
        result = self._manager.context.keyStore.native.revealSeedPhrase(
            password)
        if isinstance(result, str):
            self._parent.text = result
            return
        if result == KeyStoreError.ERROR_INVALID_PASSWORD:
            # noinspection PyUnresolvedReferences
            text = self.tr("Wrong Key Store password.")
        elif result == KeyStoreError.ERROR_SEED_NOT_FOUND:
            # noinspection PyUnresolvedReferences
            text = self.tr("Seed Phrase not found.")
        else:
            # noinspection PyUnresolvedReferences
            text = self.tr("Unknown Key Store error.")
        ConfirmPasswordErrorDialog(
            self._manager,
            self._parent,
            title=self.title,  # noqa
            text=text).open()

    def onRejected(self) -> None:
        self._parent.close.emit()


class ConfirmPasswordErrorDialog(AbstractMessageDialog):
    def onClosed(self) -> None:
        ConfirmPasswordDialog(self._manager, self._parent).open()


class KeyStoreErrorDialog(AbstractMessageDialog):
    _ERROR_MAP: Final = {
        KeyStoreError.ERROR_UNKNOWN:
            QObject().tr("Unknown Key Store error."),
        KeyStoreError.ERROR_INVALID_PASSWORD:
            QObject().tr("Wrong Key Store password."),
        KeyStoreError.ERROR_SEED_NOT_FOUND:
            QObject().tr("The seed was not found in the Key Store."),
        KeyStoreError.ERROR_SAVE_SEED:
            QObject().tr("Failed to save seed to Key Store."),
        KeyStoreError.ERROR_INVALID_SEED_PHRASE:
            QObject().tr("Invalid Seed Phrase."),
        KeyStoreError.ERROR_DERIVE_ROOT_HD_NODE:
            QObject().tr("Error derive Root HD Key."),
    }

    def __init__(
            self,
            manager: DialogManager,
            parent: AbstractDialog,
            error: KeyStoreError = KeyStoreError.ERROR_UNKNOWN):
        text = self._ERROR_MAP.get(error)
        super().__init__(
            manager,
            parent,
            title=parent.title,  # noqa
            text=text or self._ERROR_MAP[KeyStoreError.ERROR_UNKNOWN])

    def onClosed(self) -> None:
        KeyStorePasswordDialog(self._manager).open()


class KeyStoreNewPasswordDialog(AbstractDialog):
    _QML_NAME = "BKeyStoreNewPasswordDialog"

    def __init__(
            self,
            manager: DialogManager,
            generator: GenerateSeedPhrase,
            phrase: str) -> None:
        super().__init__(manager)
        self._generator = generator
        self._current_phrase = phrase

    def onPasswordAccepted(self, password: str) -> None:
        SeedPasswordDialog(
            self._manager,
            self._generator,
            self._current_phrase,
            password).open()

    def onRejected(self) -> None:
        #self._manager.context.exit(0)
        selectKeyStoreDialog(self._manager).open()


class KeyStorePasswordDialog(AbstractDialog):
    _QML_NAME = "BKeyStorePasswordDialog"

    def __init__(self, manager: DialogManager) -> None:
        super().__init__(manager)

    def onPasswordAccepted(self, password: str) -> None:
        result = self._manager.context.keyStore.native.open(password)
        if result != KeyStoreError.SUCCESS:
            KeyStoreErrorDialog(self._manager, self, result).open()

    def onRejected(self) -> None:
        selectKeyStoreDialog(self._manager).open()


class KeyStoreSelectDialog(AbstractDialog):
    _QML_NAME = "BKeyStoreSelectDialog"

    def __init__(
            self,
            manager: DialogManager) -> None:
        super().__init__(manager)

    def onKeyStoreClicked(self, path: Path) -> None:
        self._manager.context.config.filePath = Path(path)
        self._manager.context.config.load()
        self._manager.context.settings.reload()
        self.close.emit()

        KeyStorePasswordDialog(self._manager).open()

    def onGenerateAccepted(self) -> None:
        GenerateSeedPhraseDialog(self._manager, None).open()
        self.close.emit()

    def onRestoreAccepted(self) -> None:
        RestoreSeedPhraseDialog(self._manager).open()
        self.close.emit()

    def onRestoreBackupAccepted(self) -> None:
        raise NotImplementedError

    def onRejected(self) -> None:
        self._manager.context.exit(0)


class InvalidSeedPhraseDialog(KeyStoreErrorDialog):
    def __init__(
            self,
            manager: DialogManager,
            parent: SeedPasswordDialog,
            generator: Optional[GenerateSeedPhrase] = None,
            error: KeyStoreError = KeyStoreError.ERROR_INVALID_SEED_PHRASE):
        super().__init__(manager, parent, error)
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
    def text(self, value: str) -> None:
        if self.__text != value:
            self.__text = value
            # noinspection PyUnresolvedReferences
            self._textChanged.emit()

    @QProperty(bool, notify=_isValidChanged)
    def isValid(self) -> bool:
        return self.__is_valid

    @isValid.setter
    def isValid(self, value: bool) -> None:
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
            self.text = self._generator.update(None)
            self.isValid = True

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
        self.text = ""
        self._openSaltDialog()

    def onAccepted(self) -> None:
        ValidateSeedPhraseDialog(self._manager, self._generator).open()

    def onRejected(self) -> None:
        if self._child_dialog is not None:
            self._child_dialog.close.emit()
        KeyStoreSelectDialog(self._manager).open()


class SeedPasswordDialog(AbstractDialog):
    _QML_NAME = "BSeedPasswordDialog"

    def __init__(
            self,
            manager: DialogManager,
            generator: GenerateSeedPhrase,
            phrase: str,
            key_store_password: str) -> None:
        super().__init__(manager)
        self._generator = generator
        self._current_phrase = phrase
        self._key_store_password = key_store_password

    def onPasswordAccepted(self, seed_name: str, seed_password: str) -> None:
        result = self._generator.finalize(
            self._current_phrase,
            self._key_store_password,
            seed_name,
            seed_password)
        if result != KeyStoreError.SUCCESS:
            InvalidSeedPhraseDialog(
                self._manager,
                self,
                self._generator,
                result).open()

    def onRejected(self) -> None:
        result = self._generator.finalize(
            self._current_phrase,
            self._key_store_password,
            None,
            None)
        if result != KeyStoreError.SUCCESS:
            InvalidSeedPhraseDialog(
                self._manager,
                self,
                self._generator,
                result).open()


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
        self.isValid = self._generator.validate(self._current_phrase)

    def onAccepted(self) -> None:
        KeyStoreNewPasswordDialog(
            self._manager,
            self._generator,
            self._current_phrase).open()

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
        self.isValid = self._generator.validate(self._current_phrase)

    def onAccepted(self) -> None:
        KeyStoreNewPasswordDialog(
            self._manager,
            self._generator,
            self._current_phrase).open()

    def onRejected(self) -> None:
        KeyStoreSelectDialog(self._manager).open()


class RevealSeedPhraseDialog(AbstractSeedPhraseDialog):
    def __init__(self, manager: DialogManager) -> None:
        super().__init__(manager)
        self._qml_properties["type"] = self.Type.Reveal.value
        if self._manager.context.debug.isEnabled:
            self._qml_properties["readOnly"] = False
        else:
            self._qml_properties["readOnly"] = True

    def onOpened(self) -> None:
        ConfirmPasswordDialog(self._manager, self).open()


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


class AbstractTxApproveDialog(AbstractDialog):
    _QML_NAME = "BTxApproveDialog"
    _textChanged = QSignal()

    class Type(IntEnum):
        Prepare: Final = 0
        Final: Final = 1

    def __init__(self, manager: DialogManager) -> None:
        super().__init__(manager)
        self.__text = ""
        self._qml_properties["type"] = self.Type.Prepare.value

    @QProperty(str, notify=_textChanged)
    def text(self) -> str:
        return self.__text

    @text.setter
    def text(self, value: str) -> None:
        if self.__text != value:
            self.__text = value
            # noinspection PyUnresolvedReferences
            self._textChanged.emit()


class TxApproveDialog(AbstractTxApproveDialog):
    def __init__(self, manager: DialogManager, coin: Coin) -> None:
        super().__init__(manager)
        self._qml_properties["type"] = self.Type.Prepare.value
        self._qml_properties["coin"] = coin

        if self._manager.context.debug.isEnabled:
            self._qml_properties["readOnly"] = False
        else:
            self._qml_properties["readOnly"] = True

    def onOpened(self) -> None:
        ConfirmPasswordDialog(self._manager, self).open()
