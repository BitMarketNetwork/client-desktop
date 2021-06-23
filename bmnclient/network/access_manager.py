from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide2.QtNetwork import \
    QAbstractNetworkCache, \
    QNetworkAccessManager, \
    QNetworkCacheMetaData, \
    QNetworkCookieJar, \
    QNetworkProxy, \
    QNetworkReply, \
    QNetworkRequest, \
    QSsl, \
    QSslConfiguration, \
    QSslSocket

from .utils import NetworkUtils
from ..logger import Logger
from ..os_environment import Platform
from ..version import Timer

if TYPE_CHECKING:
    from typing import Final, List, Optional
    from PySide2.QtCore import QIODevice, QObject, QUrl
    from PySide2.QtNetwork import QAuthenticator, QNetworkCookie, QSslError


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
    def cookiesForUrl(self, url: QUrl) -> List[QNetworkCookie]:
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
    _OPERATION_MAP: Final = {
        QNetworkAccessManager.HeadOperation: "HEAD",
        QNetworkAccessManager.GetOperation: "GET",
        QNetworkAccessManager.PutOperation: "PUT",
        QNetworkAccessManager.PostOperation: "POST",
        QNetworkAccessManager.DeleteOperation: "DELETE",
    }

    def __init__(
            self,
            name: Optional[str] = None,
            parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self._name = name if name else "default"
        self._logger = Logger.classLogger(self.__class__, (None, self._name))

        self._cache = NullNetworkCache()
        self._cookie_jar = NullNetworkCookieJar()
        self._proxy = QNetworkProxy(QNetworkProxy.NoProxy)
        self._tls_config = self._createTlsConfiguration()
        self._http2_config = None  # TODO QHttp2Configuration not supported

        self.setAutoDeleteReplies(True)
        self.enableStrictTransportSecurityStore(False)
        self.setCache(self._cache)
        self.setCookieJar(self._cookie_jar)
        self.setProxy(self._proxy)
        self.setRedirectPolicy(QNetworkRequest.ManualRedirectPolicy)
        self.setStrictTransportSecurityEnabled(False)  # TODO
        self.setTransferTimeout(Timer.NETWORK_TRANSFER_TIMEOUT)

        self.authenticationRequired.connect(
            self.__onAuthenticationRequired)
        self.proxyAuthenticationRequired.connect(
            self.__onProxyAuthenticationRequired)
        self.encrypted.connect(
            self.__onEncrypted)
        self.finished.connect(
            self.__onFinished)
        self.sslErrors.connect(
            self.__onTlsErrors)

        if parent:
            self._logger.debug(
                "Network access manager was created for '%s'.",
                parent.objectName())
        else:
            self._logger.debug("Network access manager was created.")

    @property
    def name(self) -> str:
        return self._name

    @property
    def tlsConfiguration(self) -> QSslConfiguration:
        return self._tls_config

    @property
    def http2Configuration(self) -> None:
        raise NotImplementedError
        # return self._http2_config

    def _createTlsConfiguration(self) -> QSslConfiguration:
        if self._logger.isEnabledFor(logging.DEBUG):
            version_string = QSslSocket.sslLibraryVersionString()
            version_number = QSslSocket.sslLibraryVersionNumber()
            if version_number > 0:
                version_number = " (0x{:08x})".format(version_number)
            else:
                version_number = ""
            self._logger.debug(
                "TLS information:"
                "\n\tSupports: %s"
                "\n\tVersion:  %s%s",
                "YES" if QSslSocket.supportsSsl() else "NO",
                version_string,
                version_number)
        if not QSslSocket.supportsSsl():
            Logger.fatal("Platform doesn't support TLS.", self._logger)

        tls = QSslConfiguration()
        tls.setOcspStaplingEnabled(False)
        tls.setPeerVerifyDepth(0)  # whole certificate chain should be checked
        # TODO: Qt 5.15 + macOS, recheck after moving to Qt6
        if Platform.isDarwin:
            tls.setPeerVerifyMode(QSslSocket.AutoVerifyPeer)
            tls.setProtocol(QSsl.SecureProtocols)
        else:
            tls.setPeerVerifyMode(QSslSocket.VerifyPeer)
            tls.setProtocol(QSsl.TlsV1_2OrLater)
        tls.setSslOption(QSsl.SslOptionDisableEmptyFragments, True)
        tls.setSslOption(QSsl.SslOptionDisableSessionTickets, False)
        tls.setSslOption(QSsl.SslOptionDisableCompression, True)
        tls.setSslOption(QSsl.SslOptionDisableServerNameIndication, False)
        tls.setSslOption(QSsl.SslOptionDisableLegacyRenegotiation, True)
        tls.setSslOption(QSsl.SslOptionDisableSessionSharing, False)
        tls.setSslOption(QSsl.SslOptionDisableSessionPersistence, True)
        return tls

    def createRequest(
            self,
            op: QNetworkAccessManager.Operation,
            request: QNetworkRequest,
            outgoing_data: Optional[QIODevice] = None) -> QNetworkReply:
        self._logger.debug(
            "New request: %s %s",
            self._OPERATION_MAP.get(op, "UNKNOWN"),
            request.url().toString())
        return super().createRequest(op, request, outgoing_data)

    def __onAuthenticationRequired(
            self,
            reply: QNetworkReply,
            _: QAuthenticator) -> None:
        self._logger.warning(
            "%sAuthentication required for URL: %s",
            self._loggerReplyPrefix(reply),
            reply.url().toString())

    def __onProxyAuthenticationRequired(
            self,
            proxy: QNetworkProxy,
            _: QAuthenticator) -> None:
        self._logger.warning(
            "Authentication required for proxy %s.",
            NetworkUtils.hostPortToString(proxy.hostName(), proxy.port()))

    def __onEncrypted(self, reply: QNetworkReply) -> None:
        if self._logger.isEnabledFor(logging.DEBUG):
            tls_config = reply.sslConfiguration()
            cipher_name = tls_config.sessionCipher().name()
            # TODO empty for http2, recheck after moving to Qt6
            if cipher_name:
                self._logger.debug(
                    "%s New TLS session, cipher: %s",
                    self._loggerReplyPrefix(reply),
                    cipher_name)
            else:
                self._logger.debug(
                    "%s New TLS session.",
                    self._loggerReplyPrefix(reply))

    def __onFinished(self, reply: QNetworkReply) -> None:
        status_code = reply.error()
        if status_code != QNetworkReply.NoError:
            if status_code not in (
                    QNetworkReply.ContentAccessDenied,
                    QNetworkReply.ContentNotFoundError,
            ):
                self._logger.warning(
                    "%s Connection error: %s",
                    self._loggerReplyPrefix(reply),
                    Logger.errorString(
                        int(status_code),
                        reply.errorString()))

        if self._logger.isEnabledFor(logging.DEBUG):
            status_code = reply.attribute(
                QNetworkRequest.HttpStatusCodeAttribute)
            status_code = int(status_code) if status_code else -1
            self._logger.debug(
                "%s HTTP status code: %i",
                self._loggerReplyPrefix(reply),
                status_code)

    def __onTlsErrors(
            self,
            reply: QNetworkReply,
            error_list: List[QSslError]) -> None:
        for e in error_list:
            self._logger.error(
                "%s %s",
                self._loggerReplyPrefix(reply),
                Logger.errorString(int(e.error()), e.errorString()))

    def _loggerReplyPrefix(self, reply: QNetworkReply) -> str:
        return "[{} {}]".format(
            self._OPERATION_MAP.get(reply.operation(), "UNKNOWN"),
            reply.url().toString())
