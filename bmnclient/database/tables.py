from __future__ import annotations

from enum import Enum
from itertools import chain
from typing import TYPE_CHECKING

from ..utils.class_property import classproperty

if TYPE_CHECKING:
    from .import Database
    from typing import Final, Optional, Tuple, Type, Union


class ColumnIdEnum(Enum):
    pass


class Column:
    __slots__ = ("_name", "_definition")

    def __init__(self, name: str, definition: str) -> None:
        self._name = name
        self._definition = definition

    def __str__(self) -> str:
        return self.id + " " + self._definition

    @property
    def name(self) -> str:
        return self._name

    @property
    def id(self) -> str:
        return "\"" + self._name + "\""

    @property
    def definition(self) -> str:
        return self._definition


class AbstractTable:
    _NAME = ""
    _CONSTRAINT_LIST: Tuple[str] = tuple()

    class ColumnId(ColumnIdEnum):
        ID: Final = Column("id", "INTEGER PRIMARY KEY")

    def __init__(self, database: Database) -> None:
        self._database = database

    def create(self) -> None:
        query = ", ".join(chain(
            (str(c.value) for c in self.ColumnId),
            (c for c in self._CONSTRAINT_LIST)))
        query = f"CREATE TABLE IF NOT EXISTS {self.id} ({query})"
        self._database.execute(query)

    def upgrade(self, old_version: int) -> None:
        pass

    def close(self) -> None:
        pass

    @classproperty
    def name(cls) -> str:  # noqa
        return cls._NAME

    @classproperty
    def id(cls) -> str:  # noqa
        return "\"" + cls._NAME + "\""


class MetadataTable(AbstractTable):
    _NAME = "metadata"

    class ColumnId(ColumnIdEnum):
        ID: Final = AbstractTable.ColumnId.ID.value
        KEY: Final = Column("key", "TEXT NOT NULL UNIQUE")
        VALUE: Final = Column("value", "TEXT")

    class Key(Enum):
        VERSION: Final = "version"

    def get(
            self,
            key: Key,
            value_type: Type[Union[int, str]],
            default_value: Optional[int, str] = None) -> Optional[int, str]:
        try:
            cursor = self._database.execute(
                f"SELECT {self.ColumnId.VALUE.value.id} FROM {self.id}"
                f" WHERE {self.ColumnId.KEY.value.id}==?",
                key.value
            )
        except self._database.engine.OperationalError:
            value = default_value
        else:
            value = cursor.fetchone()
            value = value[0] if value is not None else default_value

        if value is None:
            return None

        try:
            return value_type(value)
        except (TypeError, ValueError):
            return default_value

    def set(self, key: Key, value: Optional[int, str]) -> bool:
        try:
            cursor = self._database.execute(
                f"INSERT OR REPLACE INTO {self.id} ("
                f"{self.ColumnId.KEY.value.id}, "
                f"{self.ColumnId.VALUE.value.id}) "
                "VALUES(?, ?)",
                key.value,
                str(value)
            )
        except self._database.engine.OperationalError:
            return False
        return cursor.lastrowid is not None
