
import logging

import PySide2.QtNetwork as qt_network
import PySide2.QtQml as qt_qml

log = logging.getLogger(__name__)

NOT_REPLY_TIMEOUT = 10000


class NetworkFactory(qt_qml.QQmlNetworkAccessManagerFactory):

    def __init__(self, parent=None):
        super().__init__(parent)

    def create(self, parent) -> qt_network.QNetworkAccessManager:
        log.debug(f"new network manager for {parent}")
        man = qt_network.QNetworkAccessManager(parent=parent)
        man.setTransferTimeout(NOT_REPLY_TIMEOUT)
        man.sslErrors.connect(self.__on_ssl_errors)
        return man

    def __on_ssl_errors(self, errors) -> None:
        log.warning(f"SSL errors occurred: {errors}")
