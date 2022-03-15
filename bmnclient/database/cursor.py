from __future__ import annotations

from typing import TYPE_CHECKING

import bmnsqlite3 as _engine

from .tables import AbstractTable

if TYPE_CHECKING:
    from typing import Any, Callable, Type, Union
    from .database import Database


class Cursor(_engine.Cursor):
    def __init__(self, *args, database: Database, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._database = database

    def execute(self, query, *args, **kwargs) -> Cursor:
        return self._execute(super().execute, query, *args, **kwargs)

    def executemany(self, query, *args, **kwargs) -> Cursor:
        return self._execute(super().executemany, query, *args, **kwargs)

    def executescript(self, query, *args, **kwargs) -> Cursor:
        return self._execute(super().executescript, query, *args, **kwargs)

    def _execute(self, origin: Callable, query, *args, **kwargs) -> Any:
        self._database.logQuery(query)
        try:
            cursor = origin(query, *args, **kwargs)
            assert cursor is self
            return cursor
        except (_engine.Error, _engine.Warning) as e:
            self._database.logException(e, query)
            raise

    def isTableExists(self, table: Union[str, Type[AbstractTable]]) -> bool:
        table = table.name if issubclass(table, AbstractTable) else str(table)
        self.execute(
            "SELECT COUNT(*) FROM \"sqlite_master\""
            " WHERE \"type\" == ? AND \"name\" == ?"
            " LIMIT 1",
            ("table", table))
        value = self.fetchone()
        return value is not None and value[0] > 0

    def isColumnExists(
            self,
            table: Union[str, Type[AbstractTable]],
            name: str) -> bool:

        if not self.isTableExists(table):
            return False

        table = table.name if issubclass(table, AbstractTable) else str(table)
        for value in self.execute(f"PRAGMA table_info(\"{table}\")"):
            if len(value) > 2 and value[1] == name:
                return True

        return False
