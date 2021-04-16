# JOK++
import json
from enum import auto, Enum
from io import BytesIO
from json import JSONDecodeError
from typing import Dict, List, Optional, Union

from PySide2.QtCore import QObject, QUrl
from PySide2.QtNetwork import QNetworkReply, QNetworkRequest, QSslError

from .utils import encodeUrlString
from ..logger import Logger
from ..version import Product, Timer


class AbstractQuery(QObject):  # TODO kill QObject?
    _ENCODING = Product.ENCODING

    def __init__(self) -> None:
        super().__init__()
        self._logger = Logger.getClassLogger(__name__, self.__class__)


class AbstractHttpQuery(AbstractQuery):
    class Method(Enum):
        GET = auto()
        POST = auto()

    _DEFAULT_BASE_URL: Optional[str] = None
    _DEFAULT_METHOD = Method.GET
    _DEFAULT_CONTENT_TYPE = ""

    _REQUEST_ATTRIBUTE_LIST = (
        (
            QNetworkRequest.CacheLoadControlAttribute,
            QNetworkRequest.AlwaysNetwork
        ), (
            QNetworkRequest.CacheSaveControlAttribute,
            False
        ), (
            QNetworkRequest.DoNotBufferUploadDataAttribute,
            True
        ), (
            QNetworkRequest.HttpPipeliningAllowedAttribute,
            False
        ), (
            QNetworkRequest.CookieLoadControlAttribute,
            QNetworkRequest.Manual
        ), (
            QNetworkRequest.CookieSaveControlAttribute,
            QNetworkRequest.Manual
        ), (
            QNetworkRequest.AuthenticationReuseAttribute,
            QNetworkRequest.Manual
        ), (
            QNetworkRequest.BackgroundRequestAttribute,
            False
        ), (
            QNetworkRequest.Http2AllowedAttribute,
            True
        ), (
            QNetworkRequest.EmitAllUploadProgressSignalsAttribute,
            False
        ), (
            QNetworkRequest.FollowRedirectsAttribute,
            False
        ), (
            QNetworkRequest.RedirectPolicyAttribute,
            QNetworkRequest.ManualRedirectPolicy
        ), (
            QNetworkRequest.Http2DirectAttribute,
            False
        ), (
            QNetworkRequest.AutoDeleteReplyOnFinishAttribute,
            True
        )
    )

    def __init__(self) -> None:
        super().__init__()
        self._status_code: Optional[int] = None
        self._response: Optional[QNetworkReply] = None
        self._is_success = False

    @property
    def url(self) -> str:
        return self._DEFAULT_BASE_URL

    @property
    def arguments(self) -> Dict[str, Union[int, str]]:
        return {}

    @property
    def content(self) -> bytes:
        return b""

    @property
    def contentType(self) -> str:
        return self._DEFAULT_CONTENT_TYPE

    @property
    def method(self) -> Method:
        return self._DEFAULT_METHOD

    @property
    def statusCode(self) -> Optional[int]:
        return self._status_code

    @property
    def isSuccess(self) -> bool:
        return self._is_success

    @property
    def isDummyRequest(self) -> bool:
        return self.url is None

    def runDummyRequest(self) -> None:
        assert self.isDummyRequest and self._response is None
        self.__setStatusCode(200)
        self._is_success = True
        self._onResponseFinished()

    def createRequest(self) -> Optional[QNetworkRequest]:
        # prepare full url
        url_string = self.url
        url_query = ""
        for (k, v) in self.arguments.items():
            bad_argument = False
            if not isinstance(k, str) or not isinstance(v, (str, int)):
                bad_argument = True
            else:
                k = encodeUrlString(str(k))
                v = encodeUrlString(str(v))
                if k is None or v is None:
                    bad_argument = True
            if bad_argument:
                self._logger.error(
                    "Cannot create request for URL \"%s\", "
                    + "invalid query arguments.",
                    url_string)
                return None
            if url_query:
                url_query += "&"
            url_query += k + "=" + v
        if url_query:
            url_string += "?" + url_query

        url = QUrl(url_string, QUrl.StrictMode)
        if not url.isValid():
            self._logger.error(
                "Cannot create request, invalid URL \"%s\".",
                url_string)
            return None

        # configure QNetworkRequest
        requests = QNetworkRequest(url)
        for (a, v) in self._REQUEST_ATTRIBUTE_LIST:
            requests.setAttribute(a, v)
        # TODO requests.setHttp2Configuration()
        # TODO requests.setSslConfiguration()
        requests.setMaximumRedirectsAllowed(0)
        requests.setTransferTimeout(Timer.NETWORK_TRANSFER_TIMEOUT)

        # set content type
        content_type = self.contentType
        if content_type:
            requests.setHeader(
                QNetworkRequest.ContentTypeHeader,
                content_type)

        return requests

    def setResponse(self, response: QNetworkReply) -> None:
        assert self._response is None
        response.readyRead.connect(self.__onResponseRead)
        response.finished.connect(self.__onResponseFinished)
        response.errorOccurred.connect(self.__onResponseError)
        response.sslErrors.connect(self.__onResponseTlsError)
        response.redirected.connect(self.__onResponseRedirected)
        self._is_success = False
        self._response = response

    def __setStatusCode(self, status_code: Optional[int] = None) -> None:
        if self._status_code is not None:
            return
        if status_code is None:
            status_code = self._response.attribute(
                QNetworkRequest.HttpStatusCodeAttribute)
        if status_code:
            self._status_code = int(status_code)
        else:
            self._status_code = 0
        self._logger.debug("HTTP status code: %i", self._status_code)

    def __onResponseRead(self) -> None:
        self.__setStatusCode()
        if not self._onResponseData(self._response.readAll()):
            self._response.abort()

    def __onResponseFinished(self) -> None:
        self.__setStatusCode()
        while self._response.bytesAvailable():
            self.__onResponseRead()

        if (
                self._status_code is not None
                and self._status_code > 0
                and self._response is not None
                and self._response.error() == QNetworkReply.NoError
                and self._response.isFinished()
        ):
            self._is_success = True
        else:
            self._is_success = False

        self._onResponseFinished()
        # self._response.deleteLater()
        self._response = None

    def __onResponseError(self, code: QNetworkReply.NetworkError) -> None:
        if code in (
            QNetworkReply.ContentAccessDenied,
            QNetworkReply.ContentNotFoundError,
        ):
            return

        self._logger.error(
            "Failed to read response, connection error: %s",
            Logger.errorToString(
                int(code),  # noqa
                self._response.errorString()))

    def __onResponseRedirected(self, url: QUrl) -> None:
        Logger.fatal(
            "Redirect to \"{}\" detected, but redirects was disabled."
            .format(url.toString()),
            self._logger)

    def __onResponseTlsError(
            self,
            error_list: List[QSslError]) -> None:
        for e in error_list:
            self._logger.error(
                "Failed to read response, TLS error: %s",
                Logger.errorToString(int(e.error()), e.errorString()))

    def _onResponseData(self, data: bytes) -> bool:
        raise NotImplementedError

    def _onResponseFinished(self) -> None:
        raise NotImplementedError


class AbstractHttpJsonQuery(AbstractHttpQuery):
    _DEFAULT_CONTENT_TYPE = "application/json"

    def __init__(self) -> None:
        super().__init__()
        self._json_buffer = BytesIO()

    @property
    def content(self) -> bytes:
        value = self.jsonContent
        if value:
            try:
                return json.dumps(value).encode(encoding=self._ENCODING)
            except UnicodeError as e:
                self._logger.error(
                    "Failed to encode JSON request: %s",
                    str(e))
        return b""

    @property
    def jsonContent(self) -> Optional[dict]:
        return None

    def _onResponseData(self, data) -> bool:
        # TODO limit downloaded size
        # TODO stream mode
        self._json_buffer.write(data)
        return True

    def _onResponseFinished(self) -> None:
        response = self._json_buffer.getvalue()
        self._json_buffer.close()

        if response:
            error_message = None
            try:
                response = response.decode(encoding=self._ENCODING)
                self._logger.debug("Response: %s", response)
                response = json.loads(response)
            except UnicodeError as e:
                error_message = str(e)
            except JSONDecodeError as e:
                error_message = Logger.jsonDecodeErrorToString(e)

            if error_message is not None:
                response = None
                self._logger.warning("Invalid JSON response: %s", error_message)

        if not isinstance(response, dict):
            response = None
        self._processResponse(response)

    def _processResponse(self, response: Optional[dict]) -> bool:
        raise NotImplementedError
