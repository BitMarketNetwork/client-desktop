from __future__ import annotations

from typing import TYPE_CHECKING

import bmnsqlite3 as engine

if TYPE_CHECKING:
    import logging
    from typing import Any, Callable


class Cursor(engine.Cursor):
    def __init__(self, *args, logger: logging.Logger, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._logger = logger

    def execute(self, query, *args, **kwargs) -> Cursor:
        return self._execute(super().execute, query, *args, **kwargs)

    def executemany(self, query, *args, **kwargs) -> Cursor:
        return self._execute(super().executemany, query, *args, **kwargs)

    def executescript(self, query, *args, **kwargs) -> Cursor:
        return self._execute(super().executescript, query, *args, **kwargs)

    def _execute(
            self,
            origin: Callable,
            query,
            *args,
            **kwargs) -> Any:
        self._logger.debug("Query: %s", query)
        try:
            r = origin(query, *args, **kwargs)
            assert r is not None
            return r
        except engine.Error as e:
            self._logger.error("Cursor error: %s", str(e))
            raise e
        except engine.Warning as e:
            self._logger.warning("Cursor warning: %s", str(e))
            raise e


class Connection(engine.Connection):
    def __init__(self, *args, logger: logging.Logger, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._logger = logger

    def cursor(self, factory=Cursor) -> Cursor:
        return super().cursor(
            factory=lambda *args, **kwargs: Cursor(
                *args,
                logger=self._logger,
                **kwargs)
        )
