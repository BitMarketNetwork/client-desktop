from __future__ import annotations

from enum import Enum
from itertools import chain
from typing import TYPE_CHECKING

from ...utils.class_property import classproperty

if TYPE_CHECKING:
    from typing import (
        Any,
        Dict,
        Final,
        Generator,
        Iterable,
        List,
        Optional,
        Sequence,
        Tuple,
        Type,
        Union)
    from .. import Cursor, Database
    from ...utils.serialize import Serializable


class SortOrder(str, Enum):
    ASC: Final = "ASC"
    DESC: Final = "DESC"


class Column:
    __slots__ = ("_name", "_identifier", "_definition", "_full_definition")

    def __init__(self, name: str, definition: str) -> None:
        self._name = name
        self._identifier = f"\"{self._name}\""
        self._definition = definition
        self._full_definition = f"{self._identifier} {self._definition}"

    def __str__(self) -> str:
        return self._full_definition

    @property
    def name(self) -> str:
        return self._name

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def definition(self) -> str:
        return self._definition


class ColumnEnum(Column, Enum):
    def __init__(
            self,
            name: str = "row_id",
            definition: str = "INTEGER PRIMARY KEY") -> None:
        super().__init__(name, definition)


if TYPE_CHECKING:
    ColumnValue = Tuple[Column, Union[str, int]]


class AbstractTable:
    class ColumnEnum(ColumnEnum):
        ROW_ID: Final = ()

    __NAME: str = ""
    __IDENTIFIER: str = ""
    __DEFINITION: str = ""
    _CONSTRAINT_LIST: Tuple[str, ...] = tuple()
    _UNIQUE_COLUMN_LIST: Tuple[Tuple[Column]] = tuple()

    # noinspection PyMethodOverriding
    def __init_subclass__(cls, *args, name: str, **kwargs) -> None:
        super().__init_subclass__(*args, **kwargs)
        cls.__NAME = name
        cls.__IDENTIFIER = f"\"{cls.__NAME}\""

        definition_list = cls.join(chain(
            (str(c) for c in cls.ColumnEnum),
            (c for c in cls._CONSTRAINT_LIST),
            (
                f"UNIQUE({cls.joinColumns(c)})"
                for c in cls._UNIQUE_COLUMN_LIST
            )
        ))
        cls.__DEFINITION = (
            f"CREATE TABLE IF NOT EXISTS {cls.__IDENTIFIER}"
            f" ({definition_list})"
        )

    def __init__(self, database: Database) -> None:
        self._database = database

    def __str__(self) -> str:
        return self.__DEFINITION

    @classproperty
    def name(cls) -> str:  # noqa
        return cls.__NAME

    @classproperty
    def identifier(cls) -> str:  # noqa
        return cls.__IDENTIFIER

    def open(self, cursor: Cursor) -> None:
        cursor.execute(str(self))

    def upgrade(self, cursor: Cursor, old_version: int) -> None:
        pass

    def close(self, cursor: Cursor) -> None:
        pass

    def _insertOrUpdate(
            self,
            cursor: Cursor,
            key_columns: Sequence[ColumnValue],
            data_columns: Sequence[ColumnValue],
            *,
            row_id: int = -1,
            row_id_required: bool = True) -> int:
        def columnsString(columns) -> str:
            return " and ".join(
                f"'{k.name}' == '{str(v)}'" for (k, v) in columns
            )

        if row_id > 0:
            cursor.execute(
                f"UPDATE {self.identifier}"
                f" SET {self.joinColumnsQmark(c[0] for c in data_columns)}"
                f" WHERE {self.joinColumnsQmark([self.ColumnEnum.ROW_ID])}",
                [*(c[1] for c in data_columns), row_id])
            if cursor.rowcount > 0:
                assert cursor.rowcount == 1
                return row_id

        insert_columns = self.joinColumns(
            c[0] for c in chain(key_columns, data_columns))
        cursor.execute(
            f"INSERT OR IGNORE INTO {self.identifier}"
            f" ({insert_columns})"
            f" VALUES({self.qmark(len(key_columns) + len(data_columns))})",
            [c[1] for c in chain(key_columns, data_columns)])
        del insert_columns

        if cursor.rowcount > 0:
            assert cursor.rowcount == 1
            assert cursor.lastrowid > 0
            return cursor.lastrowid

        if row_id_required:
            if row_id <= 0:
                query = (
                    f"SELECT {self.joinColumns([self.ColumnEnum.ROW_ID])}"
                    f" FROM {self.identifier}"
                    f" WHERE {self.joinQmarkAnd(c[0] for c in key_columns)}"
                    f" LIMIT 1"
                )
                for r in cursor.execute(query, [c[1] for c in key_columns]):
                    row_id = int(r[0])
                    break
                if row_id <= 0:
                    raise self._database.InsertOrUpdateError(
                        "row not found where: {}"
                        .format(columnsString(key_columns)),
                        query)
        if row_id > 0:
            key_columns = [(self.ColumnEnum.ROW_ID, row_id)]

        query = (
            f"UPDATE {self.identifier}"
            f" SET {self.joinColumnsQmark(c[0] for c in data_columns)}"
            f" WHERE {self.joinQmarkAnd(c[0] for c in key_columns)}"
        )
        cursor.execute(
            query,
            [c[1] for c in chain(data_columns, key_columns)])
        if cursor.rowcount <= 0:
            raise self._database.InsertOrUpdateError(
                "row not found where: {}"
                .format(columnsString(key_columns)),
                query)

        return row_id

    def _serialize(
            self,
            cursor: Cursor,
            source: Serializable,
            key_columns: Sequence[ColumnValue],
            custom_columns: Optional[Sequence[ColumnValue]] = None,
            **options) -> None:
        assert self.ColumnEnum.ROW_ID not in (c[0] for c in key_columns)
        source_data = source.serialize(exclude_subclasses=True, **options)

        if not custom_columns:
            custom_columns = []
            data_columns = []
        else:
            data_columns = [c for c in custom_columns]

        for column in self.ColumnEnum:
            if column.name not in source_data:
                continue
            if column in (c[0] for c in chain(key_columns, custom_columns)):
                continue
            data_columns.append((column, source_data[column.name]))

        source.rowId = self._insertOrUpdate(
            cursor,
            key_columns,
            data_columns,
            row_id=source.rowId)
        assert source.rowId > 0

    def _deserialize(
            self,
            cursor: Cursor,
            source_type: Type[Serializable],
            key_columns: Dict[Column, Any],
            order_columns: Iterable[Tuple[Column, SortOrder]] = tuple(),
            *,
            limit: int = -1,
            return_key_columns: bool = False,
            **options
    ) -> Generator[Dict[str, Union[int, str]], None, None]:
        assert self.ColumnEnum.ROW_ID not in key_columns
        column_list = [self.ColumnEnum.ROW_ID]
        for column in self.ColumnEnum:
            if column not in key_columns:
                if column.name in source_type.serializeMap:
                    column_list.append(column)

        query, query_args = self._deserializeStatement(
            column_list,
            key_columns,
            **options)

        if order_columns:
            query += f" ORDER BY {self.joinSortOrder(order_columns)}"

        if limit >= 0:
            query += f" LIMIT ?"
            query_args.append(limit)

        for result in cursor.execute(query, query_args):
            if return_key_columns:
                yield dict(chain(
                    zip(
                        (c.name for c in key_columns.keys()),
                        key_columns.values()),
                    zip(
                        (c.name for c in column_list),
                        result)
                ))
            else:
                yield dict(zip(
                    (c.name for c in column_list),
                    result)
                )

    def _deserializeStatement(
            self,
            column_list: List[Column],
            key_columns: Dict[Column, Any],
            **_options
    ) -> Tuple[str, List[Any]]:
        return (
            (
                f"SELECT {self.joinColumns(column_list)}"
                f" FROM {self.identifier}"
                f" WHERE {self.joinQmarkAnd(key_columns.keys())}"
            ),
            [*key_columns.values()]
        )

    @staticmethod
    def join(source: Iterable[str]) -> str:
        return ", ".join(source)

    @classmethod
    def joinColumns(cls, source: Iterable[Column]) -> str:
        return cls.join(s.identifier for s in source)

    @classmethod
    def joinColumnsQmark(cls, source: Iterable[Column]) -> str:
        return cls.join(f"{s.identifier} == ?" for s in source)

    @classmethod
    def joinSortOrder(cls, source: Iterable[Tuple[Column, SortOrder]]) -> str:
        return cls.join(f"{s[0].identifier} {s[1]}" for s in source)

    @staticmethod
    def joinQmarkAnd(source: Iterable[Column]) -> str:
        return " AND ".join(f"{s.identifier} == ?" for s in source)

    @classmethod
    def qmark(cls, count: int) -> str:
        return cls.join("?" * count)
