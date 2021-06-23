from __future__ import annotations
from typing import TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Slot as QSlot

if TYPE_CHECKING:
    from . import QmlApplication


class KeyStoreModel(QObject):
    def __init__(self, application: QmlApplication):
        super().__init__()
        self._application = application
