from __future__ import annotations

from typing import TYPE_CHECKING
from unittest import TestCase

from PySide6.QtCore import QEventLoop
from PySide6.QtNetwork import QNetworkReply, QNetworkRequest

from bmnclient.network.access_manager import NetworkAccessManager
from bmnclient.network.query import AbstractJsonQuery, AbstractQuery
from tests import TestApplication

if TYPE_CHECKING:
    from typing import Dict, Optional, Union

_logger = TestApplication.getLogger(__name__)


class QueryHelper:
    def __init__(self) -> None:
        self.test_arguments = None
        self.test_content = None
        self.event_loop = None

        self.response_data = None
        self.response_data_result = True
        self.response_data_called = False
        self.response_finished_called = False


class DefaultGetQuery(AbstractQuery, QueryHelper):
    _DEFAULT_URL = "https://bitmarket.network/"

    def __init__(self) -> None:
        AbstractQuery.__init__(self, name_key_tuple=())
        QueryHelper.__init__(self)

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


class DefaultPostQuery(DefaultGetQuery):
    _DEFAULT_METHOD = AbstractQuery.Method.POST
    _DEFAULT_URL = "https://bitmarket.network/_not_found_"


class BadTlsQuery(DefaultGetQuery):
    _DEFAULT_URL = "https://expired.badssl.com/"


class DummyQuery(AbstractQuery, QueryHelper):
    _DEFAULT_URL = None

    def __init__(self) -> None:
        AbstractQuery.__init__(self, name_key_tuple=())
        QueryHelper.__init__(self)

    def _onResponseData(self, data: bytes) -> bool:
        self.response_data_called = True
        return self.response_data_result

    def _onResponseFinished(self) -> None:
        self.response_finished_called = True


class DefaultJsonGetQuery(AbstractJsonQuery, QueryHelper):
    _DEFAULT_URL = "https://d1.bitmarket.network:30110/v1/sysinfo"
    _DEFAULT_CONTENT_TYPE = "application/vnd.api+json"

    def __init__(self) -> None:
        AbstractJsonQuery.__init__(self, name_key_tuple=())
        QueryHelper.__init__(self)

    @property
    def jsonContent(self) -> Optional[dict]:
        return self.test_content

    def _processResponse(self, response: Optional[dict, list]) -> None:
        self.response_data = response
        self.event_loop.exit()


class DefaultJsonPostQuery(DefaultJsonGetQuery):
    _DEFAULT_METHOD = AbstractQuery.Method.POST


class TestNetworkQuery(TestCase):
    def setUp(self) -> None:
        self._application = TestApplication()

    def tearDown(self) -> None:
        self._application.setExitEvent()

    def _run_request(self, query: AbstractQuery,) -> None:
        manager = NetworkAccessManager()

        request = query.createRequest()
        request.setSslConfiguration(manager.tlsConfiguration)
        if query.method == AbstractQuery.Method.GET:
            response = manager.get(request)
        elif query.method == AbstractQuery.Method.POST:
            # noinspection PyTypeChecker
            response = manager.post(request, query.content)
        else:
            response = None
        self.assertIsInstance(response, QNetworkReply)

        query.setResponse(response, None)
        query.event_loop = QEventLoop()
        query.event_loop.exec()
        query.event_loop = None

    def test_query(self) -> None:
        q = DefaultGetQuery()
        self.assertEqual(q.url, "https://bitmarket.network/")
        self.assertEqual(q.arguments, {})
        self.assertEqual(q.statusCode, None)
        self.assertFalse(q.isDummyRequest)

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
        q = DefaultGetQuery()
        request = q.createRequest()
        # noinspection PyProtectedMember
        for (a, v) in q._REQUEST_ATTRIBUTE_LIST:
            self.assertEqual(request.attribute(a), v)

    def test_query_run(self) -> None:
        # normal GET
        q = DefaultGetQuery()
        self.assertTrue(q.response_data_result)
        self.assertFalse(q.response_data_called)
        self.assertFalse(q.response_finished_called)
        self.assertFalse(q.isSuccess)
        self._run_request(q)
        self.assertTrue(q.isSuccess)
        self.assertEqual(q.statusCode, 200)
        self.assertTrue(q.response_data_called)
        self.assertTrue(q.response_finished_called)

        # normal POST
        q = DefaultPostQuery()
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
        q = DefaultGetQuery()
        q.response_data_result = False
        self.assertFalse(q.isSuccess)
        self._run_request(q)
        self.assertFalse(q.isSuccess)
        self.assertTrue(q.response_data_called)
        self.assertTrue(q.response_finished_called)

        # TLS error
        q = BadTlsQuery()
        self._run_request(q)
        self.assertFalse(q.isSuccess)
        self.assertFalse(q.response_data_called)
        self.assertTrue(q.response_finished_called)

    def test_dummy_query_run(self) -> None:
        q = DummyQuery()
        self.assertTrue(q.isDummyRequest)
        self.assertFalse(q.isSuccess)
        q.finishDummyRequest()
        self.assertTrue(q.isSuccess)
        self.assertFalse(q.response_data_called)
        self.assertTrue(q.response_finished_called)

    def test_json_query(self) -> None:
        q = DefaultJsonGetQuery()
        request = q.createRequest()
        header = request.header(QNetworkRequest.ContentTypeHeader)
        self.assertGreater(len(q.contentType), len("application/"))
        self.assertEqual(header, q.contentType)

        self.assertEqual(q.content, b"")
        q.test_content = {"Hello1": 1}
        self.assertEqual(q.content, b"{\"Hello1\": 1}")

    def test_json_query_run(self) -> None:
        # normal GET
        q = DefaultJsonGetQuery()
        self.assertFalse(q.isSuccess)
        self._run_request(q)
        self.assertTrue(q.isSuccess)
        self.assertIsInstance(q.response_data, dict)

        # normal POST
        q = DefaultJsonPostQuery()
        self.assertFalse(q.isSuccess)
        self._run_request(q)
        self.assertFalse(q.isSuccess)
        self.assertEqual(q.statusCode, 405)
        self.assertIsInstance(q.response_data, dict)
