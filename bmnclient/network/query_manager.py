from __future__ import annotations

from enum import auto, Enum
from typing import TYPE_CHECKING

from .access_manager import NetworkAccessManager
from .query import AbstractQuery
from ..logger import Logger

from PySide6.QtNetwork import QNetworkProxy
from PySide6.QtCore import QUrl
if TYPE_CHECKING:
    from typing import List, Optional


class NetworkQueryManager:
    class QueryRunState(Enum):
        SKIPPED = auto()
        PENDING = auto()
        FINISHED = auto()
        FAILED = auto()

    class PutStatus(Enum):
        SUCCESS = auto()
        ERROR_NOT_UNIQUE = auto()

    def __init__(self, name: str) -> None:
        self._logger = Logger.classLogger(self.__class__, (None, name))
        self._manager = NetworkAccessManager(name)
        self._queue: List[AbstractQuery] = []
        self._current_query: Optional[AbstractQuery] = None

    @property
    def name(self) -> str:
        return self._manager.name

    @property
    def proxy(self) -> QNetworkProxy:
        return self._manager.proxy

    def proxyUpdate(self, url: QUrl = None) -> None:
        self._manager.proxyUpdate(url)

    @property
    def currentQuery(self) -> Optional[AbstractQuery]:
        return self._current_query

    def isUnique(self, query: AbstractQuery) -> bool:
        if (
                self._current_query is not None
                and self._current_query.isEqualQuery(query)
        ):
            return False

        for q in self._queue:
            if q.isEqualQuery(query):
                return False

        return True

    def put(
            self,
            query: AbstractQuery,
            *,
            unique: bool = False,
            high_priority: bool = False) -> PutStatus:
        if unique and not self.isUnique(query):
            self._logger.debug("Query '%s' already in queue.", str(query))
            return self.PutStatus.ERROR_NOT_UNIQUE

        if self._current_query is None and not self._queue:
            self._logger.debug(
                "Queue is empty, starting query '%s' now.",
                str(query))
            self.__runSequence(query)
            return self.PutStatus.SUCCESS

        if high_priority:
            self._logger.debug(
                "Appending query '%s' to the top position.",
                str(query)),
            self._queue.insert(0, query)
        else:
            self._logger.debug(
                "Appending query '%s' to the bottom position.",
                str(query))
            self._queue.append(query)
        self._logger.debug("New queue size: %i", len(self._queue)),
        return self.PutStatus.SUCCESS

    def __runSingle(self, query: AbstractQuery) -> QueryRunState:
        assert self._current_query is None
        if query.skip:
            self._logger.debug("Query '%s' was skipped.", str(query))
            query.finishSkippedRequest()
            return self.QueryRunState.SKIPPED

        if query.isDummyRequest:
            self._logger.debug("Query '%s' is dummy.", str(query))
            query.finishDummyRequest()
            return self.QueryRunState.FINISHED

        self._logger.debug("Staring query '%s'.", str(query))
        request = query.createRequest()
        if request is None:
            query.finishInvalidRequest()
            return self.QueryRunState.FAILED

        request.setSslConfiguration(self._manager.tlsConfiguration)
        request.setHttp2Configuration(self._manager.http2Configuration)

        if query.method == AbstractQuery.Method.GET:
            response = self._manager.get(request)
        elif query.method == AbstractQuery.Method.POST:
            # noinspection PyTypeChecker
            response = self._manager.post(request, query.content)
        else:
            self._logger.error("Unsupported HTTP method '%s'.", query.method)
            query.finishInvalidRequest()
            return self.QueryRunState.FAILED

        self._current_query = query
        self._current_query.setResponse(response, self.__runNext)
        return self.QueryRunState.PENDING

    def __runSequence(self, query: Optional[AbstractQuery]) -> QueryRunState:
        assert self._current_query is None
        while True:
            if query is None:
                # sequence complete
                return self.QueryRunState.FINISHED
            if self.__runSingle(query) == self.QueryRunState.PENDING:
                # continue at __runNextQuery()
                return self.QueryRunState.PENDING
            if self._current_query is not None:
                # created by query.__finished_callback_list -> put()
                return self.QueryRunState.PENDING
            query = query.nextQuery

    def __runNext(self, query: AbstractQuery) -> None:
        assert query is self._current_query
        self._current_query = None

        if self.__runSequence(query.nextQuery) == self.QueryRunState.PENDING:
            return

        while self._queue:
            query = self._queue.pop(0)
            if self.__runSequence(query) == self.QueryRunState.PENDING:
                break
        self._logger.debug("Current queue size: %i", len(self._queue)),
