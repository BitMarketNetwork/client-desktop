from __future__ import annotations

from enum import auto
from typing import TYPE_CHECKING, Final, Sequence

from PySide6.QtCore import \
    QObject, \
    Slot as QSlot

from .list import AbstractListModel, RoleEnum
from ..dialogs.key_store import RevealSeedPhraseDialog, TxApproveDialog
from ....coins.abstract.coin import Coin
from ....config import ConfigSeed

if TYPE_CHECKING:
    from . import QmlApplication
    from ....key_store import KeyStore


class KeyStoreModel(AbstractListModel):
    class Role(RoleEnum):
        NAME: Final = auto()
        SEED: Final = auto()

    _ROLE_MAP: Final = {
        Role.NAME: (
            ConfigSeed.NAME.value,
            lambda c: c[ConfigSeed.NAME.value]),
        Role.SEED: (
            ConfigSeed.SEED.value,
            lambda c: c[ConfigSeed.SEED.value])
    }

    def __init__(
            self,
            application: QmlApplication,
            source_list: Sequence) -> None:
        super().__init__(
            application,
            source_list)

        self._application = application
        self._current_seed = None

    @property
    def currentSeed(self) -> str:
        return self._current_seed

    @currentSeed.setter
    def currentSeed(self, value: str):
        self._current_seed = value

    @property
    def native(self) -> KeyStore:
        return self._application.keyStore

    @QSlot()
    def onRevealSeedPhrase(self) -> None:
        # noinspection PyTypeChecker
        RevealSeedPhraseDialog(
            self._application.qmlContext.dialogManager).open()

    @QSlot(QObject)
    def onPrepareTransaction(self, coin: Coin) -> None:
        TxApproveDialog(
            self._application.qmlContext.dialogManager, coin).open()
