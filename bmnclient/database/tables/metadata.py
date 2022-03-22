from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from .table import AbstractTable, Column, ColumnEnum, ColumnValue, RowListProxy

if TYPE_CHECKING:
    from typing import Final, Optional, Type, Union


class MetadataTable(AbstractTable, name="metadata"):
    class ColumnEnum(ColumnEnum):
        ROW_ID: Final = ()
        KEY: Final = ("key", "TEXT NOT NULL UNIQUE")
        VALUE: Final = ("value", "TEXT")

    class Key(Enum):
        VERSION: Final = "version"

    def rowListProxy(self, *args, **kwargs) -> RowListProxy:
        raise NotImplementedError

    def get(
            self,
            key: Key,
            value_type: Type[Union[int, str]],
            default_value: Optional[int, str] = None) -> Optional[int, str]:
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

    def set(self, key: Key, value: Optional[int, str]) -> None:
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
