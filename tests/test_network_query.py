# JOK++
import unittest
from typing import Dict, Optional, Union

from PySide2.QtCore import QCoreApplication, QEventLoop
from PySide2.QtNetwork import QNetworkReply, QNetworkRequest

from bmnclient.network.access_manager import NetworkAccessManager
from bmnclient.network.query import HttpJsonQuery, HttpQuery
from tests import getLogger

_logger = getLogger(__name__)


class HttpQueryHelper:
    def __init__(self) -> None:
        self.test_arguments = None
        self.test_content = None
        self.event_loop = None

        self.response_data = None
        self.response_data_result = True
        self.response_data_called = False
        self.response_finished_called = False


class DefaultHttpGetQuery(HttpQuery, HttpQueryHelper):
    _DEFAULT_BASE_URL = "https://bitmarket.network/"

    def __init__(self) -> None:
        HttpQuery.__init__(self)
        HttpQueryHelper.__init__(self)

    @property
    def arguments(self) -> Dict[str, Union[int, str]]:
        if self.test_arguments is not None:
            return self.test_arguments
        else:
            return super().arguments

    @property
    def content(self) -> bytes:
        if self.test_content is not None:
            return self.test_content
        else:
            return super().content

    def _onResponseData(self, data: bytes) -> bool:
        self.response_data_called = True
        _logger.debug(
            "_onResponseData: statusCode = %i, len(data) = %i",
            self.statusCode,
            len(data))
        return self.response_data_result

    def _onResponseFinished(self) -> None:
        self.response_finished_called = True
        _logger.debug(
            "_onResponseFinished: statusCode = %i",
            self.statusCode)
        self.event_loop.exit()


class DefaultHttpPostQuery(DefaultHttpGetQuery):
    _DEFAULT_METHOD = HttpQuery.Method.POST
    _DEFAULT_BASE_URL = "https://bitmarket.network/_not_found_"


class BadTlsHttpQuery(DefaultHttpGetQuery):
    _DEFAULT_BASE_URL = "https://expired.badssl.com/"


class DummyHttpJsonGetQuery(HttpJsonQuery, HttpQueryHelper):
    _DEFAULT_BASE_URL = "https://d1.bitmarket.network:30110/v1/sysinfo"
    _DEFAULT_CONTENT_TYPE = "application/vnd.api+json"

    def __init__(self) -> None:
        HttpJsonQuery.__init__(self)
        HttpQueryHelper.__init__(self)

    @property
    def jsonContent(self) -> Optional[dict]:
        return self.test_content

    def _processResponse(self, response: Optional[dict]) -> bool:
        self.response_data = response
        self.event_loop.exit()
        return True


class DummyHttpJsonPostQuery(DummyHttpJsonGetQuery):
    _DEFAULT_METHOD = HttpQuery.Method.POST


class TestNetworkQuery(unittest.TestCase):
    application = QCoreApplication(["unittest"])

    def _run_request(self, query: HttpQuery,) -> None:
        manager = NetworkAccessManager()

        request = query.createRequest()
        if query.method == HttpQuery.Method.GET:
            response = manager.get(request)
        elif query.method == HttpQuery.Method.POST:
            # noinspection PyTypeChecker
            response = manager.post(request, query.content)
        else:
            response = None
        self.assertIsInstance(response, QNetworkReply)

        query.setResponse(response)
        query.event_loop = QEventLoop()
        query.event_loop.exec_()
        query.event_loop = None

    def test_http_query(self) -> None:
        q = DefaultHttpGetQuery()
        self.assertEqual(q.url, "https://bitmarket.network/")
        self.assertEqual(q.arguments, {})
        self.assertEqual(q.statusCode, None)

        # empty argument list
        request = q.createRequest()
        self.assertIsInstance(request, QNetworkRequest)
        self.assertEqual(request.url().toString(), q.url)

        # simple argument list
        q.test_arguments = {"a": 1}
        request = q.createRequest()
        self.assertIsInstance(request, QNetworkRequest)
        self.assertEqual(request.url().toString(), q.url + "?a=1")

        # strict argument list
        q.test_arguments = {
            "a": 1,
            "b": " spaces ",
            "spaces  ": " ",
            "&": "+"
        }
        request = q.createRequest()
        self.assertIsInstance(request, QNetworkRequest)
        self.assertEqual(
            request.url().toString(),
            q.url + "?a=1&b=+spaces+&spaces++=+&%26=%2B")

        # bad argument list
        q.test_arguments = {"a": 0.0}
        request = q.createRequest()
        self.assertIsNone(request)

        # test QNetworkRequest configuration
        q = DefaultHttpGetQuery()
        request = q.createRequest()
        # noinspection PyProtectedMember
        for (a, v) in q._REQUEST_ATTRIBUTE_LIST:
            self.assertEqual(request.attribute(a), v)

    def test_http_query_run(self) -> None:
        # normal GET
        q = DefaultHttpGetQuery()
        self.assertTrue(q.response_data_result)
        self.assertFalse(q.response_data_called)
        self.assertFalse(q.response_finished_called)
        self.assertFalse(q.isSuccess)
        self._run_request(q)
        self.assertTrue(q.isSuccess)
        self.assertTrue(q.response_data_called)
        self.assertTrue(q.response_finished_called)

        # normal POST
        q = DefaultHttpPostQuery()
        self.assertTrue(q.response_data_result)
        self.assertFalse(q.response_data_called)
        self.assertFalse(q.response_finished_called)
        self.assertFalse(q.isSuccess)
        q.test_content = b"HELLO"
        self._run_request(q)
        self.assertFalse(q.isSuccess)
        self.assertEqual(q.statusCode, 404)
        self.assertTrue(q.response_data_called)
        self.assertTrue(q.response_finished_called)

        # abort
        q = DefaultHttpGetQuery()
        q.response_data_result = False
        self.assertFalse(q.isSuccess)
        self._run_request(q)
        self.assertFalse(q.isSuccess)
        self.assertTrue(q.response_data_called)
        self.assertTrue(q.response_finished_called)

        # TLS error
        q = BadTlsHttpQuery()
        self._run_request(q)
        self.assertFalse(q.isSuccess)
        self.assertFalse(q.response_data_called)
        self.assertTrue(q.response_finished_called)

    def test_http_json_query(self) -> None:
        q = DummyHttpJsonGetQuery()
        request = q.createRequest()
        header = request.header(QNetworkRequest.ContentTypeHeader)
        self.assertGreater(len(q.contentType), len("application/"))
        self.assertEqual(header, q.contentType)

        self.assertEqual(q.content, b"")
        q.test_content = {"Hello1": 1}
        self.assertEqual(q.content, b"{\"Hello1\": 1}")

    def test_http_json_query_run(self) -> None:
        # normal GET
        q = DummyHttpJsonGetQuery()
        self.assertFalse(q.isSuccess)
        self._run_request(q)
        self.assertTrue(q.isSuccess)
        self.assertIsInstance(q.response_data, dict)

        # normal POST
        q = DummyHttpJsonPostQuery()
        self.assertFalse(q.isSuccess)
        self._run_request(q)
        self.assertFalse(q.isSuccess)
        self.assertEqual(q.statusCode, 405)
        self.assertIsInstance(q.response_data, dict)
