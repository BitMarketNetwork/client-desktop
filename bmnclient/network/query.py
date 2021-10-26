from __future__ import annotations

import json
from enum import auto, Enum
from io import BytesIO
from json import JSONDecodeError
from typing import TYPE_CHECKING

from PySide2.QtCore import QUrl
from PySide2.QtNetwork import QNetworkReply, QNetworkRequest

from .utils import NetworkUtils
from ..logger import Logger
from ..utils.string import StringUtils
from ..version import Product, Timer
from ..utils.size_unit import SizeUnit, SizeUnitConverter

if TYPE_CHECKING:
    from typing import Callable, Dict, List, Optional, Tuple, Union
    from PySide2.QtNetwork import QSslError
    from ..utils.string import ClassStringKeyTuple


class AbstractQuery:
    class Method(Enum):
        GET = auto()
        POST = auto()

    _ENCODING = Product.ENCODING
    _DEFAULT_URL: Optional[str] = None
    _DEFAULT_METHOD = Method.GET
    _DEFAULT_CONTENT_TYPE = "application/x-www-form-urlencoded"

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
            False  # TODO QNetworkRequest.encrypted not called
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

    def __init__(
            self,
            *args,
            name_key_tuple: Tuple[ClassStringKeyTuple, ...],
            **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__name_key_list = name_key_tuple
        self._logger = Logger.classLogger(self.__class__, *name_key_tuple)
        self.__status_code: Optional[int] = None
        self.__response: Optional[QNetworkReply] = None
        self.__is_success = False
        self._next_query: Optional[AbstractQuery] = None

        self.__finished_callback_list: List[Callable[[AbstractQuery], None]] = \
            []
        self.__close_callback: Optional[Callable[[AbstractQuery], None]] = \
            None

    def __str__(self) -> str:
        return StringUtils.classString(self.__class__, *self.__name_key_list)

    def isEqualQuery(self, other: AbstractQuery) -> bool:
        return (
                isinstance(other, self.__class__)
                and self.url == other.url
                and self.method == other.method
        )

    @property
    def url(self) -> Optional[str]:
        return self._DEFAULT_URL

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
        return self.__status_code

    @property
    def isSuccess(self) -> bool:
        return self.__is_success

    @property
    def nextQuery(self) -> Optional[AbstractQuery]:
        return self._next_query

    def appendFinishedCallback(
            self,
            callback: Callable[[AbstractQuery], None]) -> None:
        self.__finished_callback_list.append(callback)

    def __callFinishedCallbackList(self) -> None:
        for c in self.__finished_callback_list:
            c(self)

    def _prepareNextQuery(self) -> None:
        if self._next_query is None:
            return
        for f in self.__finished_callback_list:
            if f not in self._next_query.__finished_callback_list:
                self._next_query.__finished_callback_list.append(f)

    @property
    def skip(self) -> bool:
        return False

    def finishSkippedRequest(self) -> None:
        assert self.skip and self.__response is None
        self.__is_success = False
        self.__callFinishedCallbackList()
        self._prepareNextQuery()

    @property
    def isDummyRequest(self) -> bool:
        return self.url is None

    def finishDummyRequest(self) -> None:
        assert self.isDummyRequest and self.__response is None
        self.__setStatusCode(200)
        self.__is_success = True
        self._onResponseFinished()
        self.__callFinishedCallbackList()
        self._prepareNextQuery()

    def finishInvalidRequest(self) -> None:
        self.__is_success = False
        self.__callFinishedCallbackList()
        self._prepareNextQuery()

    def createRequest(self) -> Optional[QNetworkRequest]:
        # prepare full url
        url_string = self.url
        if not url_string:
            self._logger.error(
                "Cannot create request, empty URL.",
                url_string)
            return None

        url_query = ""
        for (k, v) in self.arguments.items():
            bad_argument = False
            if not isinstance(k, str) or not isinstance(v, (str, int)):
                bad_argument = True
            else:
                k = NetworkUtils.encodeUrlString(str(k))
                v = NetworkUtils.encodeUrlString(str(v))
                if k is None or v is None:
                    bad_argument = True
            if bad_argument:
                self._logger.error(
                    "Cannot create request for URL '%s', "
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
                "Cannot create request, invalid URL '%s'.",
                url_string)
            return None

        # configure QNetworkRequest
        requests = QNetworkRequest(url)
        for (a, v) in self._REQUEST_ATTRIBUTE_LIST:
            requests.setAttribute(a, v)
        requests.setMaximumRedirectsAllowed(0)
        requests.setTransferTimeout(Timer.NETWORK_TRANSFER_TIMEOUT)

        # set content type
        content_type = self.contentType
        if content_type:
            requests.setHeader(
                QNetworkRequest.ContentTypeHeader,
                content_type)

        return requests

    def setResponse(
            self,
            response: QNetworkReply,
            close_callback: Optional[Callable[[AbstractQuery], None]]) -> None:
        assert self.__response is None
        self.__is_success = False
        self.__response = response
        self.__close_callback = close_callback

        response.readyRead.connect(self.__onResponseRead)
        response.finished.connect(self.__onResponseFinished)
        response.redirected.connect(self.__onResponseRedirected)
        response.sslErrors.connect(self.__onTlsErrors)

    def __setStatusCode(self, status_code: Optional[int] = None) -> None:
        if self.__status_code is not None:
            return
        if status_code is None:
            status_code = self.__response.attribute(
                QNetworkRequest.HttpStatusCodeAttribute)
        self.__status_code = int(status_code) if status_code else -1
        self._logger.debug("Status code: %i", self.__status_code)

    def __onResponseRead(self) -> None:
        self.__setStatusCode()
        if not self._onResponseData(self.__response.readAll()):
            self.__response.abort()

    def __onResponseFinished(self) -> None:
        self.__setStatusCode()
        while self.__response.bytesAvailable():
            self.__onResponseRead()

        if (
                self.__status_code is not None
                and self.__status_code > 0
                and self.__response is not None
                and self.__response.error() == QNetworkReply.NoError
                and self.__response.isFinished()
        ):
            self.__is_success = True
        else:
            self.__is_success = False

        self._onResponseFinished()
        # self._response.deleteLater()
        self.__response = None
        self.__callFinishedCallbackList()
        self._prepareNextQuery()

        if self.__close_callback is not None:
            self.__close_callback(self)

    def __onResponseRedirected(self, url: QUrl) -> None:
        Logger.fatal(
            "Redirect to '{}' detected, but redirects was disabled."
                .format(url.toString()),
            self._logger)

    def __onTlsErrors(self, error_list: List[QSslError]) -> None:
        for e in error_list:
            if self._onTlsError(e):
                self.__response.ignoreSslErrors()
                break

    def _onTlsError(self, error: QSslError) -> bool:
        return False

    def _onResponseData(self, data: bytes) -> bool:
        raise NotImplementedError

    def _onResponseFinished(self) -> None:
        raise NotImplementedError


class AbstractJsonQuery(AbstractQuery):
    _DEFAULT_CONTENT_TYPE = "application/json"
    _DEFAULT_DOWNLOAD_MAX_SIZE = SizeUnitConverter.unitToSize(16, SizeUnit.MB)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._json_buffer = BytesIO()

    @property
    def content(self) -> bytes:
        value = self.jsonContent
        if value:
            try:
                value = json.dumps(value)
                self._logger.debug("JSON Request: %s", value)
                return value.encode(self._ENCODING)
            except UnicodeError as e:
                self._logger.error(
                    "Failed to encode JSON request: %s",
                    str(e))
        return b""

    @property
    def jsonContent(self) -> Optional[dict]:
        return None

    def _onResponseData(self, data) -> bool:
        # TODO stream mode
        self._logger.debug(
            "Limit download size: %d MiB",
            SizeUnitConverter.sizeToUnit(self._DEFAULT_DOWNLOAD_MAX_SIZE, SizeUnit.MB))
        if len(data) > self._DEFAULT_DOWNLOAD_MAX_SIZE:
            self._logger.error(
                "Limit download size has been reached: %d bytes",
                self._DEFAULT_DOWNLOAD_MAX_SIZE)
            return False
        self._json_buffer.write(data)
        return True

    def _onResponseFinished(self) -> None:
        response = self._json_buffer.getvalue()
        self._json_buffer.close()

        if response:
            error_message = None
            try:
                response = response.decode(self._ENCODING)
                self._logger.debug("Response: %s", response)
                response = json.loads(response)
            except UnicodeError as e:
                error_message = str(e)
            except JSONDecodeError as e:
                error_message = Logger.jsonDecodeErrorString(e)

            if error_message is not None:
                response = None
                self._logger.warning("Invalid JSON response: %s", error_message)

        if not isinstance(response, dict):
            response = None
        self._processResponse(response)

    def _processResponse(self, response: Optional[dict]) -> None:
        raise NotImplementedError
