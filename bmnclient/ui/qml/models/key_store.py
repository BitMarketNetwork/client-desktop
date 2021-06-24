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
    def revealSeedPhrase(self, password: str) -> str:
        return self._application.keyStore.revealSeedPhrase(password)

    @QProperty(bool, constant=True)
    def hasSeed(self) -> bool:
        return self._application.keyStore.hasSeed

    # noinspection PyTypeChecker
    @QSlot(str, result=int)
    def calcPasswordStrength(self, password: str) -> int:
        return self._application.keyStore.calcPasswordStrength(password)

    # noinspection PyTypeChecker
    @QSlot(str, result=bool)
    def create(self, password: str) -> bool:
        return self._application.keyStore.create(password)

    # noinspection PyTypeChecker
    @QSlot(str, result=bool)
    def open(self, password: str) -> bool:
        return self._application.keyStore.open(password)

    # noinspection PyTypeChecker
    @QSlot(str, result=bool)
    def verify(self, password: str) -> bool:
        return self._application.keyStore.verify(password)

    # noinspection PyTypeChecker
    @QSlot(result=bool)
    def reset(self) -> bool:
        return self._application.keyStore.reset()

    @QProperty(bool, constant=True)
    def isExists(self) -> bool:
        return self._application.keyStore.isExists
