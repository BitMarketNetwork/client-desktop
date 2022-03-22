from __future__ import annotations

from collections.abc import MutableSequence
from enum import Enum
from itertools import chain
from typing import TYPE_CHECKING

from ...utils import DeserializeFlag, SerializeFlag
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
    from ...utils import Serializable


class SortOrder(Enum):
    ASC: Final = "ASC"
    DESC: Final = "DESC"

    @staticmethod
    def join(source: Iterable[Tuple[Column, SortOrder]]) -> str:
        return ", ".join(f"{s[0]} {s[1].value}" for s in source)


class Column:
    __slots__ = ("_name", "_identifier", "_definition", "_full_definition")

    def __init__(self, name: str, definition: str) -> None:
        self._name = name
        self._identifier = f"\"{self._name}\""
        self._definition = definition
        self._full_definition = f"{self._identifier} {self._definition}"

    def __str__(self) -> str:
        return self._identifier

    def __repr__(self) -> str:
        return self._full_definition

    @property
    def name(self) -> str:
        return self._name

    @property
    def definition(self) -> str:
        return self._definition

    @staticmethod
    def join(source: Iterable[Column]) -> str:
        return ", ".join(str(s) for s in source)

    @classmethod
    def joinSet(cls, source: Iterable[Column]) -> str:
        return ", ".join(f"{s} = ?" for s in source)

    @classmethod
    def joinWhere(
            cls,
            source: Iterable[Column],
            separator: str = "AND",
            operator: str = "==") -> str:
        return f" {separator} ".join(f"{s} {operator} ?" for s in source)


class ColumnValue:
    __slots__ = ("_column", "value")

    def __init__(self, column: Column, value: Optional[str, int]) -> None:
        self._column = column
        self.value = value

    @property
    def column(self) -> Column:
        return self._column

    @classmethod
    def join(cls, count: int) -> str:
        return ", ".join("?" * count)

    @classmethod
    def fromSerializable(
            cls,
            source: Serializable,
            column_enum: Iterable[ColumnEnum],
            exclude_columns: Iterable[Column] = tuple()) -> List[ColumnValue]:
        source_data = source.serialize(
            SerializeFlag.DATABASE_MODE |
            SerializeFlag.EXCLUDE_SUBCLASSES)
        columns: List[ColumnValue] = []

        for column in column_enum:
            if column.name in source_data and column not in exclude_columns:
                columns.append(ColumnValue(column, source_data[column.name]))

        return columns


class ColumnEnum(Column, Enum):
    def __init__(
            self,
            name: str = "row_id",
            definition: str = "INTEGER PRIMARY KEY") -> None:
        super().__init__(name, definition)


class TableMeta(type):
    def __str__(cls) -> str:
        return cls.__str__()

    def __repr__(cls) -> str:
        return cls.__repr__()


class AbstractTable(metaclass=TableMeta):
    class ColumnEnum(ColumnEnum):
        ROW_ID: Final = ()

    __NAME: str = ""
    __IDENTIFIER: str = ""
    __DEFINITION: str = ""
    _CONSTRAINT_LIST: Tuple[str, ...] = tuple()
    _UNIQUE_COLUMN_LIST: Tuple[Tuple[Column]] = tuple()

    def __init_subclass__(cls, *args, **kwargs) -> None:
        name = kwargs.pop("name")
        super().__init_subclass__(*args, **kwargs)
        cls.__NAME = name
        cls.__IDENTIFIER = f"\"{cls.__NAME}\""

        definition_list = ", ".join(chain(
            (repr(c) for c in cls.ColumnEnum),
            (c for c in cls._CONSTRAINT_LIST),
            (f"UNIQUE({Column.join(c)})" for c in cls._UNIQUE_COLUMN_LIST)
        ))
        cls.__DEFINITION = (
            f"CREATE TABLE IF NOT EXISTS {cls.__IDENTIFIER}"
            f" ({definition_list})"
        )

    def __init__(self, database: Database) -> None:
        self._database = database

    @classmethod
    def __str__(cls) -> str:
        return cls.__IDENTIFIER

    @classmethod
    def __repr__(cls) -> str:
        return cls.__DEFINITION

    @classproperty
    def name(cls) -> str:  # noqa
        return cls.__NAME

    @property
    def database(self) -> Database:
        return self._database

    def open(self, cursor: Cursor) -> None:
        cursor.execute(repr(self))

    def upgrade(self, cursor: Cursor, old_version: int) -> None:
        pass

    def close(self, cursor: Cursor) -> None:
        pass

    def rowListProxy(self, *args, **kwargs) -> RowListProxy:
        raise NotImplementedError

    def insert(self, columns: Sequence[ColumnValue]) -> int:
        with self._database.transaction(allow_in_transaction=True) as c:
            c.execute(
                f"INSERT OR IGNORE INTO {self} ("
                f"{Column.join(c.column for c in columns)})"
                f" VALUES ("
                f"{ColumnValue.join(len(columns))})",
                [c.value for c in columns])
            if c.rowcount > 0:
                assert c.rowcount == 1
                assert c.lastrowid > 0
                return c.lastrowid
        return -1

    def update(self, row_id: int, columns: Sequence[ColumnValue]) -> bool:
        assert row_id > 0
        with self._database.transaction(allow_in_transaction=True) as c:
            c.execute(
                f"UPDATE {self}"
                f" SET {Column.joinSet(c.column for c in columns)}"
                f" WHERE {self.ColumnEnum.ROW_ID} == ?",
                [*(c.value for c in columns), row_id])
            if c.rowcount > 0:
                assert c.rowcount == 1
                return True
        return False

    def save(
            self,
            row_id: int,
            key_columns: Sequence[ColumnValue],
            data_columns: Sequence[ColumnValue]) -> int:
        with self._database.transaction(allow_in_transaction=True) as c:
            # row id is defined and row found
            if row_id > 0 and self.update(row_id, data_columns):
                return row_id

            # row id not defined or row id not found (deleted row)
            new_row_id = self.insert([*chain(key_columns, data_columns)])
            if new_row_id > 0:
                return new_row_id

            # row with UNIQUE columns already exists

            # row not defined
            if row_id <= 0:
                c.execute(
                    f"SELECT {self.ColumnEnum.ROW_ID}"
                    f" FROM {self}"
                    f" WHERE {Column.joinWhere(c.column for c in key_columns)}"
                    f" LIMIT 1",
                    [c.value for c in key_columns])
                value = c.fetchone()
                if value is None or value[0] <= 0:
                    row_id = -1
                else:
                    row_id = value[0]

            # row id is defined and row found
            if row_id > 0 and self.update(row_id, data_columns):
                return row_id

            raise self._database.SaveError(
                "row in table '{}' not found where: {}"
                .format(
                    self,
                    " and ".join(
                        f"{c.column} == '{str(c.value)}'"
                        for c in key_columns
                    )))

    def load(self,
             row_id: int,
             key_columns: Sequence[ColumnValue],
             data_columns: Sequence[ColumnValue]) -> int:
        with self._database.transaction(allow_in_transaction=True) as c:
            # select by row_id
            if row_id > 0:
                c.execute(
                    f"SELECT {Column.join(c.column for c in data_columns)}"
                    f" FROM {self}"
                    f" WHERE {self.ColumnEnum.ROW_ID} == ?"
                    f" LIMIT 1",
                    [row_id])
                value = c.fetchone()
                if value is None:
                    row_id = -1

            # select by key_columns
            if row_id <= 0:
                columns = [
                    self.ColumnEnum.ROW_ID,
                    *(c.column for c in key_columns)]
                c.execute(
                    f"SELECT {Column.join(columns)}"
                    f" FROM {self}"
                    f" WHERE {Column.joinWhere(c.column for c in key_columns)}"
                    f" LIMIT 1",
                    [c.value for c in key_columns])
                value = c.fetchone()
                if value is None or value[0] <= 0:
                    return -1
                row_id = value[0]
                value = value[1:]

        for i in range(len(data_columns)):
            data_columns[i].value = value[i]
        return row_id

    def _serialize(
            self,
            source: Serializable,
            key_columns: Sequence[ColumnValue],
            custom_columns: Sequence[ColumnValue] = tuple()) -> bool:
        assert self.ColumnEnum.ROW_ID not in (c.column for c in key_columns)

        if not custom_columns:
            custom_columns = []
            data_columns = []
        else:
            data_columns = [c for c in custom_columns]

        data_columns += ColumnValue.fromSerializable(
            source,
            self.ColumnEnum,
            (c.column for c in chain(key_columns, custom_columns)))

        source.rowId = self.save(source.rowId, key_columns, data_columns)
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
            query += f" ORDER BY {SortOrder.join(order_columns)}"

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
                f"SELECT {Column.join(column_list)}"
                f" FROM {self}"
                f" WHERE {Column.joinWhere(key_columns.keys())}"
            ),
            [*key_columns.values()]
        )


# Performance: https://www.sqlite.org/autoinc.html
class RowListProxy(MutableSequence):
    def __init__(
            self,
            *,
            type_: Type[Serializable],
            type_args: Optional[Sequence[Any]] = None,
            table: AbstractTable,
            where_expression: Optional[str] = None,
            where_args: Optional[Sequence[Union[str, int]]],
            order_columns: Optional[Sequence[Tuple[Column, SortOrder]]] = None
    ) -> None:
        self._type = type_
        self._type_args = type_args if type_args else []

        self._table = table
        self._where_args = where_args if where_args else tuple()

        self._column_list = []
        for column in self._table.ColumnEnum:
            if column.name in self._type.serializeMap:
                self._column_list.append(column)
        if self._table.ColumnEnum.ROW_ID not in self._column_list:
            self._column_list.insert(0, self._table.ColumnEnum.ROW_ID)

        column_expression = Column.join(self._column_list)
        order_expression = SortOrder.join(
            order_columns if order_columns else
            [(self._table.ColumnEnum.ROW_ID, SortOrder.ASC)])
        if where_expression:
            where_expression = " WHERE" + where_expression

        self._query_length = (
            f"SELECT COUNT(*)"
            f" FROM {self._table}"
            f"{where_expression}")
        self._query_iter = (
            f"SELECT {column_expression}"
            f" FROM {self._table}"
            f"{where_expression}"
            f" ORDER BY {order_expression}")
        self._query_getitem = (
            f"SELECT {column_expression}"
            f" FROM {self._table}"
            f"{where_expression}"
            f" ORDER BY {order_expression}"
            f" LIMIT 1 OFFSET ?")

    def _deserialize(
            self,
            row: Tuple[Optional[str, int]]) -> Optional[Serializable]:
        return self._type.deserialize(
            DeserializeFlag.DATABASE_MODE,
            dict(zip((c.name for c in self._column_list), row)),
            *self._type_args)

    def __len__(self) -> int:
        with self._table.database.transaction(allow_in_transaction=True) as c:
            c.execute(self._query_length, self._where_args)
            row = c.fetchone()
            if row:
                assert isinstance(row[0], int)
                return row[0]
        return 0

    def __iter__(self) -> Generator[Serializable, None, None]:
        with self._table.database.transaction(allow_in_transaction=True) as c:
            for row in c.execute(self._query_iter, self._where_args):
                yield self._deserialize(row)

    def __getitem__(self, index: int) -> Optional[Serializable]:
        with self._table.database.transaction(allow_in_transaction=True) as c:
            c.execute(self._query_getitem, [*self._where_args, index])
            row = c.fetchone()
            if not row:
                raise IndexError()
            return self._deserialize(row)

    def __setitem__(self, index: int, value) -> None:
        # TODO
        raise NotImplementedError

    def __delitem__(self, index: int) -> None:
        # TODO
        raise NotImplementedError

    def insert(self, index: int, value: Serializable) -> None:
        # TODO
        raise NotImplementedError

    def append(self, value: Serializable) -> None:
        # TODO
        raise NotImplementedError
