# JOK++
import logging
from typing import List, Optional

from PySide2.QtCore import QIODevice, QObject, QUrl
from PySide2.QtNetwork import \
    QAbstractNetworkCache, \
    QAuthenticator, \
    QNetworkAccessManager, \
    QNetworkCacheMetaData, \
    QNetworkCookie, \
    QNetworkCookieJar, \
    QNetworkProxy, \
    QNetworkReply, \
    QNetworkRequest, \
    QSslError

from . import hostPortToString
from ..logger import Logger
from ..version import Timer


class AbstractNetworkCache(QAbstractNetworkCache):
    def cacheSize(self) -> int:
        return 0

    def data(self, url: QUrl) -> Optional[QIODevice]:
        return None

    def insert(self, device: Optional[QIODevice]) -> None:
        pass

    def metaData(self, url: QUrl) -> QNetworkCacheMetaData:
        return QNetworkCacheMetaData()

    def prepare(self, meta_data: QNetworkCacheMetaData) -> Optional[QIODevice]:
        return None

    def remove(self, url: QUrl) -> bool:
        return False

    def updateMetaData(self, meta_data: QNetworkCacheMetaData) -> None:
        pass

    def clear(self) -> None:
        pass


class NullNetworkCache(AbstractNetworkCache):
    pass


class AbstractNetworkCookieJar(QNetworkCookieJar):
    def cookiesForUrl(self, url) -> List[QNetworkCookie]:
        return []

    def deleteCookie(self, cookie: QNetworkCookie) -> bool:
        return False

    def insertCookie(self, cookie: QNetworkCookie) -> bool:
        return False

    def setCookiesFromUrl(
            self,
            cookie_list: List[QNetworkCookie],
            url: QUrl) -> bool:
        return False

    def updateCookie(self, cookie: QNetworkCookie) -> bool:
        return False


class NullNetworkCookieJar(AbstractNetworkCookieJar):
    pass


class NetworkAccessManager(QNetworkAccessManager):
    def __init__(
            self,
            name: Optional[str] = None,
            parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self._name = name if name else "default"
        self._logger = Logger.getClassLogger(
            __name__,
            self.__class__,
            self._name)

        self._cache = NullNetworkCache()
        self._cookie_jar = NullNetworkCookieJar()
        self._proxy = QNetworkProxy(QNetworkProxy.NoProxy)

        self.setAutoDeleteReplies(False)
        self.enableStrictTransportSecurityStore(False)
        self.setCache(self._cache)
        self.setCookieJar(self._cookie_jar)
        self.setProxy(self._proxy)
        self.setRedirectPolicy(QNetworkRequest.ManualRedirectPolicy)
        self.setStrictTransportSecurityEnabled(False)  # TODO
        self.setTransferTimeout(Timer.NETWORK_READ_TIMEOUT)

        self.authenticationRequired.connect(
            self._onAuthenticationRequired)
        self.proxyAuthenticationRequired.connect(
            self._onProxyAuthenticationRequired)
        self.encrypted.connect(
            self._onEncrypted)
        self.sslErrors.connect(
            self._onSslErrors)

        if parent:
            self._logger.debug(
                "\"%s\" network access manager was created for \"%s\".",
                self._name,
                parent.objectName())
        else:
            self._logger.debug(
                "\"%s\" network access manager ws created.",
                self._name)

    def _onAuthenticationRequired(
            self,
            reply: QNetworkReply,
            authenticator: QAuthenticator) -> None:
        self._logger.warning(
            "%sAuthentication required for URL: %s",
            self._loggerReplyPrefix(reply),
            reply.url().toString())

    def _onProxyAuthenticationRequired(
            self,
            proxy: QNetworkProxy,
            authenticator: QAuthenticator) -> None:
        self._logger.warning(
            "Authentication required for proxy %s.",
            hostPortToString(proxy.hostName(), proxy.port()))

    def _onEncrypted(self, reply: QNetworkReply) -> None:
        if self._logger.isEnabledFor(logging.DEBUG):
            tls_config = reply.sslConfiguration()
            self._logger.debug(
                "%sNew TLS session, cipher \"%s\".",
                self._loggerReplyPrefix(reply),
                tls_config.sessionCipher().name())

    def _onSslErrors(
            self,
            reply: QNetworkReply,
            error_list: List[QSslError]) -> None:
        for e in error_list:
            self._logger.error(
                "%s%s",
                self._loggerReplyPrefix(reply),
                Logger.errorToString(int(e.error()), e.errorString()))

    @classmethod
    def _loggerReplyPrefix(cls, reply: QNetworkReply) -> str:
        return \
            hostPortToString(reply.url().host(), reply.url().port(443)) \
            + ": "
