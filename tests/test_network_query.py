# JOK++
import unittest
from typing import Dict, Union, Optional

from PySide2.QtCore import QCoreApplication, QEventLoop
from PySide2.QtNetwork import QNetworkRequest, QNetworkReply

from bmnclient.network.query import HttpJsonQuery, HttpQuery
from bmnclient.network.access_manager import NetworkAccessManager

from tests import getLogger
_logger = getLogger(__name__)


class HttpQueryHelper:
    def __init__(self) -> None:
        self.test_arguments = None
        self.event_loop = None

        self.response_data_result = True
        self.response_data_called = False
        self.response_finished_called = False


class DefaultHttpQuery(HttpQuery, HttpQueryHelper):
    _DEFAULT_BASE_URL = "https://google.com/"

    def __init__(self) -> None:
        HttpQuery.__init__(self)
        HttpQueryHelper.__init__(self)

    @property
    def arguments(self) -> Dict[str, Union[int, str]]:
        if self.test_arguments is not None:
            return self.test_arguments
        else:
            return super().arguments

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


class BadTlsHttpQuery(DefaultHttpQuery):
    _DEFAULT_BASE_URL = "https://expired.badssl.com/"


class DummyHttpJsonQuery(HttpJsonQuery):
    _DEFAULT_BASE_URL = "https://google.com/"

    def __init__(self) -> None:
        super().__init__()
        self.test_content = None

    @property
    def jsonContent(self) -> Optional[dict]:
        return self.test_content


class TestNetworkQuery(unittest.TestCase):
    application = QCoreApplication(["unittest"])

    def _run_request(self, query: HttpQuery,) -> None:
        manager = NetworkAccessManager()

        request = query.createRequest()
        if query.method == HttpQuery.Method.GET:
            response = manager.get(request)
        elif query.method == HttpQuery.Method.POST:
            response = manager.post(request, query.content)
        else:
            response = None
        self.assertIsInstance(response, QNetworkReply)

        query.setResponse(response)
        query.event_loop = QEventLoop()
        query.event_loop.exec_()

    def test_http_query(self) -> None:
        q = DefaultHttpQuery()
        self.assertEqual(q.url, "https://google.com/")
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
        q = DefaultHttpQuery()
        request = q.createRequest()
        # noinspection PyProtectedMember
        for (a, v) in q._REQUEST_ATTRIBUTE_LIST:
            self.assertEqual(request.attribute(a), v)

    def test_http_query_run(self) -> None:
        # normal
        q = DefaultHttpQuery()
        self.assertTrue(q.response_data_result)
        self.assertFalse(q.response_data_called)
        self.assertFalse(q.response_finished_called)
        self._run_request(q)
        self.assertTrue(q.response_data_called)
        self.assertTrue(q.response_finished_called)

        # abort
        q = DefaultHttpQuery()
        q.response_data_result = False
        self._run_request(q)
        self.assertTrue(q.response_data_called)
        self.assertTrue(q.response_finished_called)

        # TLS error
        q = BadTlsHttpQuery()
        self._run_request(q)
        self.assertFalse(q.response_data_called)
        self.assertTrue(q.response_finished_called)

    def test_http_json_query(self) -> None:
        q = DummyHttpJsonQuery()
        request = q.createRequest()
        header = request.header(QNetworkRequest.ContentTypeHeader)
        self.assertGreater(len(q.contentType), len("application/"))
        self.assertEqual(header, q.contentType)

        self.assertEqual(q.content, b"")
        q.test_content = {"Hello1": 1}
        self.assertEqual(q.content, b"{\"Hello1\": 1}")
