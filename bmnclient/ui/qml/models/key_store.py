from __future__ import annotations

from typing import TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Slot as QSlot

if TYPE_CHECKING:
    from typing import Optional
    from . import QmlApplication


class KeyStoreModel(QObject):
    def __init__(self, application: QmlApplication):
        super().__init__()
        self._application = application

    # noinspection PyTypeChecker
    @QSlot(str, result=str)
    def prepareGenerateSeedPhrase(self, language: str = None) -> str:
        return self._application.keyStore.prepareGenerateSeedPhrase(language)

    # noinspection PyTypeChecker
    @QSlot(str, result=str)
    def updateGenerateSeedPhrase(self, salt: Optional[str]) -> str:
        return self._application.keyStore.updateGenerateSeedPhrase(salt)

    # noinspection PyTypeChecker
    @QSlot(str, result=bool)
    def validateGenerateSeedPhrase(self, phrase: str) -> bool:
        return self._application.keyStore.validateGenerateSeedPhrase(phrase)

    # noinspection PyTypeChecker
    @QSlot(str, result=bool)
    def finalizeGenerateSeedPhrase(self, phrase: str) -> bool:
        return self._application.keyStore.finalizeGenerateSeedPhrase(phrase)

    # noinspection PyTypeChecker
    @QSlot(str, result=bool)
    def prepareRestoreSeedPhrase(self, language: str = None) -> bool:
        return self._application.keyStore.prepareRestoreSeedPhrase(language)

    # noinspection PyTypeChecker
    @QSlot(str, result=bool)
    def validateRestoreSeedPhrase(self, phrase: str) -> bool:
        return self._application.keyStore.validateRestoreSeedPhrase(phrase)

    # noinspection PyTypeChecker
    @QSlot(str, result=bool)
    def finalizeRestoreSeedPhrase(self, phrase: str) -> bool:
        return self._application.keyStore.finalizeRestoreSeedPhrase(phrase)

    # noinspection PyTypeChecker
    @QSlot(str, result=str)
    def revealSeedPhrase(self, password: str):
        return self._application.keyStore.revealSeedPhrase(password)

    @QProperty(bool, constant=True)
    def hasSeed(self) -> bool:
        return self._application.keyStore.hasSeed()

    # noinspection PyTypeChecker
    @QSlot(str, result=int)
    def calcPasswordStrength(self, password: str) -> int:
        return self._application.keyStore.calcPasswordStrength(password)

    # noinspection PyTypeChecker
    @QSlot(str, result=bool)
    def createPassword(self, password: str) -> bool:
        return self._application.keyStore.createPassword(password)

    # noinspection PyTypeChecker
    @QSlot(str, result=bool)
    def applyPassword(self, password: str) -> bool:
        return self._application.keyStore.applyPassword(password)

    # noinspection PyTypeChecker
    @QSlot(str, result=bool)
    def verifyPassword(self, password: str) -> bool:
        return self._application.keyStore.verifyPassword(password)

    # noinspection PyTypeChecker
    @QSlot(result=bool)
    def resetPassword(self) -> bool:
        return self._application.keyStore.resetPassword()

    @QProperty(bool, constant=True)
    def hasPassword(self) -> bool:
        return self._application.keyStore.hasPassword()
