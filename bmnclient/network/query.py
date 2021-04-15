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


class HttpQuery(AbstractQuery):
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
            False  # TODO
        )
    )

    def __init__(self) -> None:
        super().__init__()
        self._status_code: Optional[int] = None
        self._request: Optional[QNetworkRequest] = None
        self._response: Optional[QNetworkReply] = None

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

    @statusCode.setter
    def statusCode(self, value: int):
        if self._status_code is None:
            self._status_code = value
        else:
            raise AttributeError("status is already set.")

    def createRequestData(self) -> Optional[dict]:
        return {}

    def onResponseData(self, data: bytes) -> bool:
        raise NotImplementedError

    def onResponseFinished(self) -> None:
        raise NotImplementedError


class HttpJsonQuery(HttpQuery):
    def __init__(self) -> None:
        super().__init__()
        self._json_buffer = BytesIO()

    def onResponseData(self, data) -> bool:
        # TODO limit downloaded size
        # TODO stream mode
        self._json_buffer.write(data)
        return True

    def onResponseFinished(self) -> None:
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
        self.processResponse(response)

    def processResponse(self, response: Optional[dict]) -> None:
        raise NotImplementedError
