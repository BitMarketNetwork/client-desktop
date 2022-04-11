from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import (
    Property as QProperty,
    QObject,
    Signal as QSignal)

from ....version import Product

if TYPE_CHECKING:
    from .. import QmlApplication


class UpdateModel(QObject):
    __stateChanged = QSignal()

    def __init__(self, application: QmlApplication) -> None:
        super().__init__()
        self._application = application
        self._update_available = False
        self._update_version: str = ""
        self._update_url: str = ""

    @QProperty(bool, notify=__stateChanged)
    def available(self) -> bool:
        self._update_version = Product.VERSION_UPDATE_STRING
        self._update_url = Product.VERSION_UPDATE_URL
        if Product.VERSION_STRING != self._update_version:
            return True
        return False

    @QProperty(str, notify=__stateChanged)
    def version(self) -> str:
        return self._update_version

    @QProperty(str, notify=__stateChanged)
    def url(self) -> str:
        return self._update_url
