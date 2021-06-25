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
    if context.keyStore.isExists:
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
        dialog_name = dialog.qmlName if dialog.qmlName else dialog.__name__
        for n in dir(dialog):
            if n.startswith("on") and callable(getattr(dialog, n, None)):
                properties["callbacks"].append(dialog_name + "." + n)

        # noinspection PyUnresolvedReferences
        self.openDialog.emit(dialog_name, properties)

    @QSlot(str, str, list)
    def onResult(
            self,
            qml_name: str,
            callback_name: str,
            callback_args: List[str, int]) -> None:
        try:
            dialog_name, callback_name = callback_name.split(".", 1)
        except ValueError:
            Logger.fatal(
                "Invalid dialog callback '{}', '{}'.".format(
                    qml_name,
                    callback_name),
                self._logger)
            return

        dialog = globals().get(dialog_name)
        if (
                dialog is None
                or not isinstance(dialog, type)
                or not issubclass(dialog, AbstractDialog)
        ):
            Logger.fatal(
                "Undefined dialog '{}', '{}'.".format(
                    qml_name,
                    dialog_name),
                self._logger)
            return

        dialog = dialog(self._context)
        callback = getattr(dialog, callback_name, None)
        if not callable(callback):
            Logger.fatal(
                "Undefined dialog callback '{}', '{}.{}'.".format(
                    qml_name,
                    dialog_name,
                    callback_name),
                self._logger)
            return
        callback(*callback_args)
