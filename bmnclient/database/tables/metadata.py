from __future__ import annotations

from enum import Enum

from .table import Column, ColumnEnum, ColumnValue, Table


class MetadataTable(Table, name="metadata"):
    class ColumnEnum(ColumnEnum):
        ROW_ID = ()
        KEY = ("key", "TEXT NOT NULL UNIQUE")
        VALUE = ("value", "TEXT")

    class Key(Enum):
        VERSION = "version"

    def get(
            self,
            key: Key,
            value_type: type(int) | type(str),
            default_value: int | str | None = None) -> int | str | None:
        with self._database.transaction(allow_in_transaction=True) as c:
            try:
                c.execute(
                    f"SELECT {self.ColumnEnum.VALUE}"
                    f" FROM {self}"
                    f" WHERE {self.ColumnEnum.KEY} == ?"
                    f" LIMIT 1",
                    [key.value])
            except self._database.engine.OperationalError:
                value = default_value
            else:
                value = c.fetchone()
                value = value[0] if value is not None else default_value

        if value is None:
            return None

        try:
            return value_type(value)
        except (TypeError, ValueError):
            return default_value

    def set(self, key: Key, value: int | str | None) -> None:
        with self._database.transaction(allow_in_transaction=True) as c:
            c.execute(
                f"UPDATE {self}"
                f" SET {Column.joinSet([self.ColumnEnum.VALUE])}"
                f" WHERE {self.ColumnEnum.KEY} == ?",
                [value, key.value])
            if c.rowcount <= 0:
                columns = [self.ColumnEnum.KEY, self.ColumnEnum.VALUE]
                c.execute(
                    f"INSERT INTO {self} ("
                    f"{Column.join(columns)})"
                    f" VALUES ({ColumnValue.join(len(columns))})",
                    [key.value, value])
            assert c.rowcount == 1
