from __future__ import annotations

from collections.abc import MutableSequence
from enum import Enum
from itertools import chain
from typing import TYPE_CHECKING

from ...utils import DeserializeFlag, Serializable, SerializeFlag
from ...utils.class_property import classproperty

if TYPE_CHECKING:
    from typing import (
        Any,
        Callable,
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

    def __repr__(self) -> str:
        return f"{self._column.name}: {self.value}"

    @property
    def column(self) -> Column:
        return self._column

    @classmethod
    def join(cls, count: int) -> str:
        return ", ".join("?" * count)


class ColumnEnum(Column, Enum):
    def __init__(
            self,
            name: str = "row_id",
            definition: str = "INTEGER PRIMARY KEY") -> None:
        super().__init__(name, definition)

    @classmethod
    def __getitem__(cls, name: str) -> Column:
        for column in cls:
            if column.name == name:
                return column
        raise KeyError(
            f"column with name '{name}' not found in enum '{cls.__name__}'")

    @classmethod
    def get(cls, name: str) -> Optional[Column]:
        for column in cls:
            if column.name == name:
                return column
        return None


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
    _UNIQUE_COLUMN_LIST: Tuple[Tuple[Column, ...], ...] = tuple()

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
                f"UPDATE OR IGNORE {self}"
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
            data_columns: Sequence[ColumnValue],
            *,
            fallback_search: bool = False) -> int:
        with self._database.transaction(allow_in_transaction=True) as c:
            # row id is defined and row found
            if row_id > 0:
                if self.update(row_id, data_columns):
                    return row_id
                if not fallback_search:
                    return -1

            # row id not defined or row id not found (deleted row)
            new_row_id = self.insert([*key_columns, *data_columns])
            if new_row_id > 0:
                return new_row_id
            if not fallback_search:
                return -1

            # row with UNIQUE columns already exists

            # row not defined
            if key_columns:
                c.execute(
                    f"SELECT {self.ColumnEnum.ROW_ID}"
                    f" FROM {self}"
                    f" WHERE {Column.joinWhere(c.column for c in key_columns)}"
                    f" LIMIT 1",
                    [c.value for c in key_columns])
                value = c.fetchone()
                if value is not None and value[0] >= 0:
                    row_id = value[0]
                    if row_id > 0 and self.update(row_id, data_columns):
                        return row_id

            raise self._database.engine.IntegrityError(
                "row in table '{}' not found where: {}"
                .format(
                    self,
                    ", ".join(
                        f"{c.column} == '{str(c.value)}'" for c in key_columns)
                ))

    def load(
            self,
            row_id: int,
            key_columns: Sequence[ColumnValue],
            data_columns: Sequence[ColumnValue],
            *,
            fallback_search: bool = False) -> int:
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
                    if not fallback_search:
                        return -1
                    row_id = -1

            # select by key_columns
            if row_id <= 0:
                if not key_columns:
                    return -1
                columns = [
                    self.ColumnEnum.ROW_ID,
                    *(c.column for c in data_columns)]
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

        for c, v in zip(data_columns, value):
            c.value = v
        return row_id

    def remove(
            self,
            row_id: int,
            key_columns: Sequence[ColumnValue],
            *,
            fallback_search: bool = False) -> bool:
        with self._database.transaction(allow_in_transaction=True) as c:
            if row_id > 0:
                c.execute(
                    f"DELETE FROM {self}"
                    f" WHERE {self.ColumnEnum.ROW_ID} == ?"
                    f" LIMIT 1",
                    [row_id])
                if c.rowcount > 0:
                    assert c.rowcount == 1
                    return True
                if not fallback_search:
                    return False
            if key_columns:
                c.execute(
                    f"DELETE FROM {self}"
                    f" WHERE {Column.joinWhere(c.column for c in key_columns)}",
                    [c.value for c in key_columns])
                if c.rowcount > 0:
                    return True
        return False


class AbstractSerializableTable(AbstractTable, name=""):
    _KEY_COLUMN_LIST: \
        Tuple[Tuple[Column, Callable[[Serializable], None], ...]] = tuple()

    def _keyColumns(self, object_: Serializable) -> Tuple[ColumnValue, ...]:
        columns = tuple(
            ColumnValue(c[0], c[1](object_))
            for c in self._KEY_COLUMN_LIST)
        return tuple() if any(c.value is None for c in columns) else columns

    def rowListProxy(self, *args, **kwargs) -> RowListProxy:
        raise NotImplementedError

    def saveSerializable(
            self,
            object_: Serializable,
            *,
            use_row_id: bool = True,
            fallback_search: bool = False) -> int:
        key_columns = self._keyColumns(object_)
        if not key_columns:
            return -1

        source_data = object_.serialize(
            SerializeFlag.DATABASE_MODE |
            SerializeFlag.EXCLUDE_SUBCLASSES)
        data_columns: List[ColumnValue] = []

        for name, value in source_data.items():
            column = self.ColumnEnum.get(name)
            if column and column not in key_columns:
                data_columns.append(ColumnValue(column, value))

        row_id = self.save(
            object_.rowId if use_row_id else -1,
            key_columns,
            data_columns,
            fallback_search=fallback_search)
        if row_id <= 0:
            raise self._database.engine.IntegrityError(
                "failed to save serializable object '{}'"
                .format(object_.__class__.__name__))
        if use_row_id:
            object_.rowId = row_id

        return row_id

    def loadSerializable(
            self,
            object_: Union[Serializable, Type[Serializable]],
            *cls_args,
            use_row_id: bool = True,
            fallback_search: bool = False) -> Optional[Serializable]:
        key_columns = self._keyColumns(object_)
        if not key_columns:
            return None
        data_columns: List[ColumnValue] = []
        for name in object_.serializeMap.keys():
            column = self.ColumnEnum.get(name)
            if column and column not in key_columns:
                data_columns.append(ColumnValue(column, None))

        if isinstance(object_, Serializable):
            row_id = self.load(
                object_.rowId if use_row_id else -1,
                key_columns,
                data_columns,
                fallback_search=fallback_search)
            if row_id > 0:
                object_.deserializeUpdate(
                    DeserializeFlag.DATABASE_MODE,
                    {c.column.name: c.value for c in data_columns})
                if use_row_id:
                    object_.rowId = row_id
            elif use_row_id and object_.rowId > 0:
                raise self._database.engine.IntegrityError(
                    "failed to load serializable object '{}'"
                    .format(object_.__class__.__name__))
        elif issubclass(object_, Serializable):
            row_id = self.load(
                -1,
                key_columns,
                data_columns,
                fallback_search=fallback_search)
            if row_id > 0:
                object_ = object_.deserialize(
                    DeserializeFlag.DATABASE_MODE,
                    {c.column.name: c.value for c in data_columns},
                    *cls_args,
                    row_id=row_id if use_row_id else -1)
        else:
            row_id = -1

        return object_ if row_id > 0 else None

    def completeSerializable(
            self,
            object_: Serializable,
            row_id: int,
            kwargs: Dict[str, Any]) -> int:
        key_columns = self._keyColumns(object_)
        if not key_columns:
            return -1
        data_columns = []
        for name in object_.serializeMap.keys():
            if name not in kwargs:
                column = self.ColumnEnum.get(name)
                if column is not None:
                    data_columns.append(ColumnValue(column, None))
        if not data_columns:
            return 0

        row_id = self.load(row_id, key_columns, data_columns)
        if row_id <= 0:
            return -1

        object_.rowId = row_id
        for c in data_columns:
            kwargs[c.column.name] = object_.deserializeProperty(
                DeserializeFlag.DATABASE_MODE,
                object_,
                c.column.name,
                c.value)
        return len(data_columns)

    def removeSerializable(
            self,
            object_: Serializable,
            *,
            use_row_id: bool = True,
            fallback_search: bool = False) -> int:
        key_columns = self._keyColumns(object_)
        if not key_columns:
            return -1
        result = self.remove(
            object_.rowId if use_row_id else -1,
            key_columns,
            fallback_search=fallback_search)
        if use_row_id:
            object_.rowId = -1
        return result


# Performance: https://www.sqlite.org/autoinc.html
class RowListProxy(MutableSequence):
    def __init__(
            self,
            *,
            type_: Type[Serializable],
            type_args: Optional[Sequence[Any]] = None,
            table: AbstractSerializableTable,
            where_expression: Optional[str] = None,
            where_args: Optional[Sequence[Union[str, int]]],
            order_columns: Optional[Sequence[Tuple[Column, SortOrder]]] = None
    ) -> None:
        self._type = type_
        self._type_args = type_args if type_args else []

        self._table = table
        self._where_args = where_args if where_args else []

        self._column_list: List[Column] = [self._table.ColumnEnum.ROW_ID]
        for name in self._type.serializeMap.keys():
            column = self._table.ColumnEnum.get(name)
            if column:
                self._column_list.append(column)

        column_expression = Column.join(self._column_list)
        order_expression = SortOrder.join(
            order_columns if order_columns else
            [(self._table.ColumnEnum.ROW_ID, SortOrder.ASC)])
        if where_expression:
            where_expression = " WHERE " + where_expression

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
            row: Tuple[Optional[str, int], ...]) -> Optional[Serializable]:
        it = iter(zip((c.name for c in self._column_list), row))
        row_id = next(it)[1]

        return self._type.deserialize(
            DeserializeFlag.DATABASE_MODE,
            dict(it),
            *self._type_args,
            row_id=row_id)

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
        raise NotImplementedError

    def __delitem__(self, index: int) -> None:
        raise NotImplementedError

    def insert(self, index: int, value: Serializable) -> None:
        raise NotImplementedError

    def append(self, value: Serializable) -> None:
        raise NotImplementedError
