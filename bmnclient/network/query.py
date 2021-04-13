# JOK++
import json
from enum import auto, Enum
from io import BytesIO
from json import JSONDecodeError
from typing import Optional

from PySide2.QtCore import QObject

from ..logger import Logger
from ..version import Product


class AbstractQuery(QObject):  # TODO kill QObject?
    _ENCODING = Product.ENCODING

    def __init__(self) -> None:
        super().__init__()
        self._logger = Logger.getClassLogger(__name__, self.__class__)


class HttpQuery(AbstractQuery):
    class Method(Enum):
        GET = auto()
        POST = auto()

    _BASE_URL = None
    _METHOD = Method.GET

    def __init__(self) -> None:
        super().__init__()
        self._status_code: Optional[int] = None

    @property
    def url(self) -> str:
        return self._BASE_URL

    @property
    def method(self) -> Method:
        return self._METHOD

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
                response = "1" + response.decode(encoding=self._ENCODING)
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
