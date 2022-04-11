from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal

import json
from PySide6.QtNetwork import QNetworkReply, QNetworkRequest
from PySide6.QtCore import QEventLoop

from ....version import Product
#from ....network.services.github import GithubNewReleasesApiQuery
from ....version import Product

from ....network.query import AbstractJsonQuery, AbstractQuery

if TYPE_CHECKING:
    from .. import QmlApplication
    from typing import Dict, Optional, Union

class UpdateModel(QObject):

    __stateChanged = QSignal()

    def __init__(self, application: QmlApplication) -> None:
        super().__init__()
        self._application = application
        self._update_available = False
        self._update_version: str = ''
        self._update_link: str = ''

    @QProperty(bool, notify=__stateChanged)
    def available(self) -> bool:
        self._update_version = Product.VERSION_UPDATE_STRING
        self._update_link = Product.VERSION_UPDATE_URL
        if Product.VERSION_STRING != self._update_version:
            return True
        return False

    @QProperty(str, notify=__stateChanged)
    def text(self) -> str:
        text = "New version "+self._update_version+" available!"
        return text

    @QProperty(str, notify=__stateChanged)
    def link(self) -> str:
        return self._update_link
