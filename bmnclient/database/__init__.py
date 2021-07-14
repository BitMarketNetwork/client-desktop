from __future__ import annotations

from typing import TYPE_CHECKING

import bmnsqlite3 as engine

from .wrappers import Connection
from ..logger import Logger

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Final, Optional
    from ..application import CoreApplication


class Database:
    # https://sqlite.org/pragma.html
    _PRAGMA_LIST: Final = (
        "automatic_index = OFF",
        "case_sensitive_like = OFF",
        "encoding = 'UTF-8'",
        "foreign_keys = ON",
        "main.journal_mode = DELETE",
        "temp_store = MEMORY",
    )

    def __init__(
            self,
            application: CoreApplication,
            file_path: Path) -> None:
        self._application = application
        self._file_path = file_path

        self._logger = Logger.classLogger(
            self.__class__,
            (None, self._file_path.name))
        self._logger.debug("%s version: %s", engine.__name__, engine.version)
        self._logger.debug("SQLite version: %s", engine.sqlite_version)

        self._connection: Optional[engine.Connection] = None

    @property
    def filePath(self) -> Path:
        return self._file_path

    @property
    def isOpen(self) -> bool:
        return self._connection is not None

    def open(self) -> bool:
        try:
            engine.enable_callback_tracebacks(self._application.isDebugMode)
            self._connection = engine.connect(
                self._file_path,
                timeout=0,
                detect_types=0,
                isolation_level="DEFERRED",
                check_same_thread=True,
                factory=lambda *args, **kwargs: Connection(
                    *args,
                    logger=self._logger,
                    **kwargs),
                cached_statements=100,
                uri=False)  # noqa TODO type checking
            with self._connection:
                for pragma in self._PRAGMA_LIST:
                    self._connection.execute("PRAGMA " + pragma)
        except (engine.Error, engine.Warning) as e:
            self._connection = None
            self._logger.error("Failed to open database: %s", str(e))
            return False
        return True

    def close(self) -> bool:
        if self._connection is None:
            return True
        try:
            self._connection.close()
        except (engine.Warning, engine.Error) as e:
            self._logger.error("Failed to close database: %s", str(e))
            return False
        self._connection = None
        self._logger.debug("Database was closed successfully.")
        return True

    def remove(self) -> bool:
        if not self.close():
            return False
        if self._file_path.exists():
            try:
                self._file_path.unlink()
            except OSError as e:
                self._logger.error("Failed to remove database: %s", str(e))
                return False
        return True
