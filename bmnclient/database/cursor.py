from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import bmnsqlite3 as _engine

from .tables import Table

if TYPE_CHECKING:
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

    def _execute(self, origin: Callable, query, *args, **kwargs) -> ...:
        self._database.logQuery(query)
        try:
            cursor = origin(query, *args, **kwargs)
            assert cursor is self
            return cursor
        except (_engine.Error, _engine.Warning) as e:
            self._database.logException(e, query)
            raise

    @staticmethod
    def __tableToName(table: str | type(Table)) -> str:
        if isinstance(table, str):
            return table
        if issubclass(table, Table) or isinstance(table, Table):
            return table.name
        raise TypeError

    def isTableExists(self, table: str | type(Table)) -> bool:
        self.execute(
            'SELECT COUNT(*) FROM "sqlite_master"'
            ' WHERE "type" == ? AND "name" == ?'
            " LIMIT 1",
            ("table", self.__tableToName(table)),
        )
        value = self.fetchone()
        return bool(value is not None and value[0] > 0)

    def isColumnExists(self, table: str | type(Table), name: str) -> bool:
        if not self.isTableExists(table):
            return False
        for value in self.execute(
            f'PRAGMA table_info("{self.__tableToName(table)}")'
        ):
            if len(value) > 2 and value[1] == name:
                return True
        return False
