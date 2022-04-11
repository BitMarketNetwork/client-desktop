from __future__ import annotations

from PySide6.QtCore import Property as QProperty, QObject, Signal as QSignal

from ....version import Product, tupleToVersionString


class UpdateModel(QObject):
    __stateChanged = QSignal()

    def __init__(self) -> None:
        super().__init__()
        self._version = Product.VERSION
        self._url = Product.VERSION_UPDATE_URL

    @QProperty(bool, notify=__stateChanged)
    def isAvailable(self) -> bool:
        return bool(self._version > Product.VERSION)

    @QProperty(str, notify=__stateChanged)
    def version(self) -> str:
        return tupleToVersionString(self._version)

    @QProperty(str, notify=__stateChanged)
    def url(self) -> str:
        return self._url

    def set(self, version: tuple[int, ...], url: str) -> None:
        if self._version < version:
            self._version = version
            self._url = url
            # noinspection PyUnresolvedReferences
            self.__stateChanged.emit()
