# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide2.QtCore import \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot

from ...logger import Logger

if TYPE_CHECKING:
    from typing import Type
    from . import QmlContext


def _askKeyStorePassword(context: QmlContext) -> None:
    if context.keyStore.hasPassword:
        context.dialogManager.open(BKeyStorePasswordDialog)
    else:
        context.dialogManager.open(BKeyStoreNewPasswordDialog)


class AbstractDialog:
    def __init__(self, context: QmlContext) -> None:
        self._context = context

    def onRejected(self) -> None:
        self._context.exit(0)


class BAlphaDialog(AbstractDialog):
    def onAccepted(self) -> None:
        _askKeyStorePassword(self._context)


class BKeyStoreNewPasswordDialog(AbstractDialog):
    def onPasswordReady(self) -> None:
        _askKeyStorePassword(self._context)


class BKeyStorePasswordDialog(AbstractDialog):
    def onResetWalletAccepted(self) -> None:
        _askKeyStorePassword(self._context)

    def onPasswordReady(self) -> None:
        if not self._context.keyStore.hasSeed:
            self._context.dialogManager.open(BNewSeedDialog)


class BNewSeedDialog(AbstractDialog):
    pass


class BQuitDialog(AbstractDialog):
    def onAccepted(self) -> None:
        self._context.exit(0)

    def onRejected(self) -> None:
        pass


class DialogManager(QObject):
    openDialog = QSignal(str, "QVariantMap")  # connected to QML frontend

    def __init__(self, context: QmlContext) -> None:
        super().__init__()
        self._logger = Logger.classLogger(self.__class__)
        self._context = context

    def open(self, dialog: Type[AbstractDialog]) -> None:
        properties = {
            "callbacks": []
        }
        for n in dir(dialog):
            if n.startswith("on") and callable(getattr(dialog, n, None)):
                properties["callbacks"].append(n)
        # noinspection PyUnresolvedReferences
        self.openDialog.emit(dialog.__name__, properties)

    @QSlot(str, str)
    def onResult(self, name: str, callback_name: str) -> None:
        dialog = globals().get(name)
        if (
                dialog is None
                or not isinstance(dialog, type)
                or not issubclass(dialog, AbstractDialog)
        ):
            Logger.fatal(
                "Undefined dialog '{}'.".format(name),
                self._logger)
            return
        dialog = dialog(self._context)
        callback = getattr(dialog, callback_name, None)
        if not callable(callback):
            Logger.fatal(
                "Undefined dialog callback '{}.{}'.".format(
                    name,
                    callback_name),
                self._logger)
            return
        callback()
