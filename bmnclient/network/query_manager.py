# JOK++
from __future__ import annotations

from enum import auto, Enum
from typing import List, Optional

from .access_manager import NetworkAccessManager
from .query import AbstractQuery
from ..logger import Logger


class NetworkQueryManager:
    class QueryRunState(Enum):
        SKIPPED = auto()
        PENDING = auto()
        FINISHED = auto()
        FAILED = auto()

    def __init__(self, name: str) -> None:
        self._logger = Logger.getClassLogger(
            __name__,
            self.__class__,
            name)

        self._manager = NetworkAccessManager(name)
        self._queue: List[AbstractQuery] = []
        self._current_query: Optional[AbstractQuery] = None

    def put(
            self,
            query: AbstractQuery,
            *,
            unique=False,
            high_priority=False) -> bool:
        if unique:
            found = False
            if type(self._current_query) == type(query):
                found = True
            else:
                for q in self._queue:
                    if type(q) == type(query):
                        break
            if found:
                self._logger.debug("Query \"%s\" already in queue.", str(query))
                return False

        if self._current_query is None:
            self._logger.debug(
                "Queue is empty, starting query \"%s\" now.",
                str(query))
            self._run(query)
            return True

        if high_priority:
            self._logger.debug(
                "Appending query \"%s\" to the top position.",
                str(query)),
            self._queue.insert(0, query)
        else:
            self._logger.debug(
                "Appending query \"%s\" to the bottom position.",
                str(query))
            self._queue.append(query)
        self._logger.debug("New queue size: %i", len(self._queue)),
        return True

    def _run(self, query: AbstractQuery) -> QueryRunState:
        assert self._current_query is None
        if query.skip:
            self._logger.debug("Query \"%s\" was skipped.", str(query))
            return self.QueryRunState.SKIPPED

        if query.isDummyRequest:
            self._logger.debug("Query \"%s\" is dummy.", str(query))
            query.runDummyRequest()
            return self.QueryRunState.FINISHED

        self._logger.debug("Staring query \"%s\".", str(query))
        request = query.createRequest()
        if request is None:
            return self.QueryRunState.FAILED

        # request.setHttp2Configuration(self._manager.http2Configuration)
        request.setSslConfiguration(self._manager.tlsConfiguration)

        if query.method == AbstractQuery.Method.GET:
            response = self._manager.get(request)
        elif query.method == AbstractQuery.Method.POST:
            # noinspection PyTypeChecker
            response = self._manager.post(request, query.content)
        else:
            self._logger.error("Unsupported HTTP method: %s", query.method)
            return self.QueryRunState.FAILED

        query.setResponse(response)
        query.putFinishedCallback(self._onQueryFinished)
        self._current_query = query
        return self.QueryRunState.PENDING

    def _onQueryFinished(self, query: AbstractQuery) -> None:
        assert query == self._current_query
        self._current_query = None

        while self._queue:
            query = self._queue.pop(0)
            if self._run(query) == self.QueryRunState.PENDING:
                break
        self._logger.debug("Current queue size: %i", len(self._queue)),
