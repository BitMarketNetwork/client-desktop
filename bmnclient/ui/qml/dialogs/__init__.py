from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from PySide2.QtCore import \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot

from ....logger import Logger

if TYPE_CHECKING:
    from typing import Dict, Final, List, Optional, Union
    from .. import QmlContext
    QmlProperties = Dict[str, Union[str, int]]


class AbstractDialog(QObject):
    _QML_NAME: Optional[str] = None
    forceActiveFocus = QSignal()
    reject = QSignal()

    def __init__(
            self,
            manager: DialogManager,
            *,
            title: Optional[str] = None) -> None:
        super().__init__()
        self._manager = manager
        self._qml_properties: QmlProperties = {
            "context": self
        }

        if title is not None:
            self._qml_properties["title"] = title

    @property
    def qmlName(self) -> Optional[str]:
        return self._QML_NAME

    @property
    def qmlProperties(self) -> QmlProperties:
        return self._qml_properties

    def open(self) -> None:
        self._manager.open(self)


class AbstractMessageDialog(AbstractDialog):
    _QML_NAME = "BMessageDialog"

    class Type(IntEnum):
        Information: Final = 0
        AskYesNo: Final = 1

    def __init__(
            self,
            manager: DialogManager,
            *,
            type_: Type = Type.Information,
            title: Optional[str] = None,
            text: str) -> None:
        super().__init__(manager, title=title)
        self._qml_properties["type"] = type_.value
        self._qml_properties["text"] = text


class DialogManager(QObject):
    openDialog = QSignal(str, "QVariantMap")  # connected to QML frontend

    def __init__(self, context: QmlContext) -> None:
        super().__init__()
        self._logger = Logger.classLogger(self.__class__)
        self._context = context
        self._opened_dialog_list: Dict[int, AbstractDialog] = {}
        self._opened_dialog_next_id = 1

    @property
    def context(self) -> QmlContext:
        return self._context

    def open(self, dialog: AbstractDialog) -> None:
        dialog_id = self._opened_dialog_next_id
        assert dialog_id not in self._opened_dialog_list
        self._opened_dialog_next_id += 1
        self._opened_dialog_list[dialog_id] = dialog

        if dialog.qmlName:
            qml_name = dialog.qmlName
        else:
            qml_name = dialog.__class__.__name__

        options = {
            "id": dialog_id,
            "callbacks": [],
            "properties": dialog.qmlProperties
        }
        for n in dir(dialog):
            if n.startswith("on") and callable(getattr(dialog, n, None)):
                options["callbacks"].append(n)

        # noinspection PyUnresolvedReferences
        self.openDialog.emit(qml_name, options)

    @QSlot(int, str, list)
    def onResult(
            self,
            dialog_id: int,
            callback_name: str,
            callback_args: List[Union[str, int]]) -> None:
        assert dialog_id in self._opened_dialog_list
        dialog = self._opened_dialog_list[dialog_id]
        callback = getattr(dialog, callback_name, None)
        callback(*callback_args)

    @QSlot(int)
    def onDestruction(self, dialog_id: int) -> None:
        assert dialog_id in self._opened_dialog_list
        self._logger.debug(
            "onDestruction: %i, %s",
            dialog_id,
            self._opened_dialog_list[dialog_id].__class__.__name__)
        del self._opened_dialog_list[dialog_id]
