from __future__ import annotations

from enum import Enum
from itertools import chain
from typing import TYPE_CHECKING

from ..utils.class_property import classproperty

if TYPE_CHECKING:
    from typing import (
        Any,
        Dict,
        Final,
        Generator,
        Iterable,
        List,
        Optional,
        Tuple,
        Type,
        Union
    )
    from . import Cursor, Database
    from ..coins.abstract import Coin
    from ..utils.serialize import Serializable


def _stringList(source_list: Iterable[str]) -> str:
    return ", ".join(source_list)


def _columnList(
        *source_list: ColumnEnum,
        with_qmark: bool = False) -> str:
    source_list = map(lambda s: s.value.identifier, source_list)
    if with_qmark:
        source_list = map(lambda s: f"{s} = ?", source_list)
    return _stringList(source_list)


def _whereColumnList(*source_list: ColumnEnum) -> str:
    source_list = map(lambda s: f"{s.value.identifier} == ?", source_list)
    return " AND ".join(source_list)


def _orderColumnList(*source_list: Dict[ColumnEnum, Order]) -> str:
    source_list = map(
        lambda t: f"{t[0].value.identifier} {t[1].value}",
        source_list)
    return _stringList(source_list)


def _qmarkList(count: int) -> str:
    return _stringList("?" * count)


class Order(Enum):
    ASC: Final = "ASC"
    DESC: Final = "DESC"


class ColumnEnum(Enum):
    pass


class ColumnDefinition:
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


class AbstractTable:
    class Column(ColumnEnum):
        # compatible with utils.serialize.Serializable.rowId
        ROW_ID: Final = ColumnDefinition("row_id", "INTEGER PRIMARY KEY")

    __NAME: str = ""
    __IDENTIFIER: str = ""
    _CONSTRAINT_LIST: Tuple[str] = tuple()
    _UNIQUE_COLUMN_LIST: Tuple[Tuple[Column]] = tuple()

    # noinspection PyMethodOverriding
    def __init_subclass__(cls, *args, name: str, **kwargs) -> None:
        super().__init_subclass__(*args, **kwargs)
        cls.__NAME = name
        cls.__IDENTIFIER = f"\"{cls.__NAME}\""

        definition_list = _stringList(chain(
            (str(c.value) for c in cls.Column),
            (c for c in cls._CONSTRAINT_LIST),
            (f"UNIQUE({_columnList(*c)})" for c in cls._UNIQUE_COLUMN_LIST)
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
            key_columns: Dict[Column, Any],
            data_columns: Dict[Column, Any],
            *,
            row_id: int = -1,
            row_id_required: bool = True) -> int:
        assert (
                set(data_columns.keys()) - set(key_columns.keys())
                == set(data_columns.keys())
        )

        def columnsString(columns) -> str:
            return " and ".join(
                f"'{k.value.name}' == '{str(v)}'" for (k, v) in columns.items()
            )

        if row_id > 0:
            cursor.execute(
                f"UPDATE {self.identifier}"
                f" SET {_columnList(*data_columns.keys(), with_qmark=True)}"
                f" WHERE {self.Column.ROW_ID.value.identifier} == ?",
                (*data_columns.values(), row_id))
            if cursor.rowcount > 0:
                assert cursor.rowcount == 1
                return row_id

        cursor.execute(
            f"INSERT OR IGNORE INTO {self.identifier}"
            f" ({_columnList(*key_columns.keys(), *data_columns.keys())})"
            f" VALUES({_qmarkList(len(key_columns) + len(data_columns))})",
            (*key_columns.values(), *data_columns.values()))

        if cursor.rowcount > 0:
            assert cursor.rowcount == 1
            assert cursor.lastrowid > 0
            return cursor.lastrowid

        if row_id_required:
            if row_id <= 0:
                query = (
                    f"SELECT {_columnList(self.Column.ROW_ID)}"
                    f" FROM {self.identifier}"
                    f" WHERE {_whereColumnList(*key_columns.keys())}"
                    f" LIMIT 1"
                )
                for r in cursor.execute(query, (*key_columns.values(), )):
                    row_id = int(r[0])
                    break
                if row_id <= 0:
                    raise self._database.InsertOrUpdateError(
                        "row not found".format(columnsString(key_columns)),
                        query)
        if row_id > 0:
            key_columns = {self.Column.ROW_ID: row_id}

        query = (
            f"UPDATE {self.identifier}"
            f" SET {_columnList(*data_columns.keys(), with_qmark=True)}"
            f" WHERE {_whereColumnList(*key_columns.keys())}"
        )
        cursor.execute(query, (*data_columns.values(), *key_columns.values()))
        if cursor.rowcount <= 0:
            raise self._database.InsertOrUpdateError("row not found", query)

        return row_id

    def _serialize(
            self,
            cursor: Cursor,
            source: Serializable,
            key_columns: Dict[Column, Any],
            custom_columns: Optional[Dict[Column, Any]] = None,
            **options) -> None:
        assert self.Column.ROW_ID not in key_columns
        source_data = source.serialize(
            exclude_subclasses=True,
            **options)
        if custom_columns is None:
            custom_columns = {}
            data_columns = {}
        else:
            data_columns = custom_columns.copy()

        for column in self.Column:
            if column not in key_columns and column not in custom_columns:
                if column.value.name in source_data:
                    data_columns[column] = source_data[column.value.name]

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
            order_columns: Dict[Column, Order],
            *,
            limit: int = -1,
            return_key_columns: bool = False,
            **options
    ) -> Generator[Dict[str, Union[int, str]], None, None]:
        assert self.Column.ROW_ID not in key_columns
        column_list = [self.Column.ROW_ID]
        for column in self.Column:
            if column not in key_columns:
                if column.value.name in source_type.serializeMap:
                    column_list.append(column)

        query, query_args = self._deserializeStatement(
            column_list,
            key_columns,
            **options)

        if order_columns:
            query += f" ORDER BY {_orderColumnList(*order_columns.items())}"

        if limit >= 0:
            query += f" LIMIT ?"
            query_args.append(limit)

        for result in cursor.execute(query, query_args):
            if return_key_columns:
                yield dict(chain(
                    zip(
                        (c.value.name for c in key_columns.keys()),
                        key_columns.values()),
                    zip(
                        (c.value.name for c in column_list),
                        result)
                ))
            else:
                yield dict(zip(
                    (c.value.name for c in column_list),
                    result)
                )

    def _deserializeStatement(
            self,
            column_list: List[ColumnEnum],
            key_columns: Dict[Column, Any],
            **options
    ) -> Tuple[str, List[Any]]:
        return (
            (
                f"SELECT {_columnList(*column_list)}"
                f" FROM {self.identifier}"
                f" WHERE {_whereColumnList(*key_columns.keys())}"
            ),
            [*key_columns.values()]
        )


class MetadataTable(AbstractTable, name="metadata"):
    class Column(ColumnEnum):
        ROW_ID: Final = AbstractTable.Column.ROW_ID.value
        KEY: Final = ColumnDefinition("key", "TEXT NOT NULL UNIQUE")
        VALUE: Final = ColumnDefinition("value", "TEXT")

    class Key(Enum):
        VERSION: Final = "version"

    def get(
            self,
            cursor: Cursor,
            key: Key,
            value_type: Type[Union[int, str]],
            default_value: Optional[int, str] = None) -> Optional[int, str]:
        try:
            cursor.execute(
                f"SELECT {_columnList(self.Column.VALUE)}"
                f" FROM {self.identifier}"
                f" WHERE {self.Column.KEY.value.identifier} == ?"
                f" LIMIT 1",
                (key.value, )
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

    def set(self, cursor: Cursor, key: Key, value: Optional[int, str]) -> None:
        self._insertOrUpdate(
            cursor,
            {self.Column.KEY: key.value},
            {self.Column.VALUE: str(value)},
            row_id_required=False
        )


class CoinListTable(AbstractTable, name="coins"):
    class Column(ColumnEnum):
        ROW_ID: Final = AbstractTable.Column.ROW_ID.value

        NAME: Final = ColumnDefinition(
            "name",
            "TEXT NOT NULL UNIQUE")
        IS_ENABLED: Final = ColumnDefinition(
            "is_enabled",
            "INTEGER NOT NULL")

        HEIGHT: Final = ColumnDefinition(
            "height",
            "INTEGER NOT NULL")
        VERIFIED_HEIGHT: Final = ColumnDefinition(
            "verified_height",
            "INTEGER NOT NULL")

        OFFSET: Final = ColumnDefinition(
            "offset",
            "TEXT NOT NULL")
        UNVERIFIED_OFFSET: Final = ColumnDefinition(
            "unverified_offset",
            "TEXT NOT NULL")
        UNVERIFIED_HASH: Final = ColumnDefinition(
            "unverified_hash",
            "TEXT NOT NULL")

    def deserialize(self, cursor: Cursor, coin: Coin) -> bool:
        result = next(
            self._deserialize(
                cursor,
                type(coin),
                {self.Column.NAME: coin.name},
                {},
                limit=1,
                return_key_columns=True),
            None)
        if result is None:
            return False

        if not coin.deserializeUpdate(result):
            self._database.logDeserializeError(type(coin), result)
            return False
        else:
            assert coin.rowId > 0
            return True

    def serialize(self, cursor: Cursor, coin: Coin) -> None:
        self._serialize(
            cursor,
            coin,
            {self.Column.NAME: coin.name})
        assert coin.rowId > 0


class AddressListTable(AbstractTable, name="addresses"):
    class Column(ColumnEnum):
        ROW_ID: Final = AbstractTable.Column.ROW_ID.value
        COIN_ROW_ID: Final = ColumnDefinition(
            "coin_row_id",
            "INTEGER NOT NULL")

        NAME: Final = ColumnDefinition(
            "name",
            "TEXT NOT NULL")
        BALANCE: Final = ColumnDefinition(
            "balance",
            "INTEGER NOT NULL")
        TX_COUNT: Final = ColumnDefinition(
            "tx_count",
            "INTEGER NOT NULL")

        LABEL: Final = ColumnDefinition(
            "label",
            "TEXT NOT NULL")
        COMMENT: Final = ColumnDefinition(
            "comment",
            "TEXT NOT NULL")
        KEY: Final = ColumnDefinition(
            "key",
            "TEXT")

        HISTORY_FIRST_OFFSET: Final = ColumnDefinition(
            "history_first_offset",
            "TEXT NOT NULL")
        HISTORY_LAST_OFFSET: Final = ColumnDefinition(
            "history_last_offset",
            "TEXT NOT NULL")

    _CONSTRAINT_LIST = (
        f"FOREIGN KEY ({_columnList(Column.COIN_ROW_ID)})"
        f" REFERENCES {CoinListTable.identifier}"
        f" ({_columnList(CoinListTable.Column.ROW_ID)})"
        f" ON DELETE CASCADE",
    )
    _UNIQUE_COLUMN_LIST = (
        (Column.COIN_ROW_ID, Column.NAME),
    )

    # TODO dynamic interface with coin.txList, address.txList
    def deserializeAll(self, cursor: Cursor, coin: Coin) -> bool:
        assert coin.rowId > 0

        error = False
        for result in self._deserialize(
                cursor,
                coin.Address,
                {self.Column.COIN_ROW_ID: coin.rowId},
                {}
        ):
            address = coin.Address.deserialize(result, coin)
            if address is None:
                error = True
                self._database.logDeserializeError(coin.Address, result)
            else:
                assert address.rowId > 0
                coin.appendAddress(address)
        return not error

    def serialize(self, cursor: Cursor, address: Coin.Address) -> None:
        assert address.coin.rowId > 0
        assert not address.isNullData

        self._serialize(
            cursor,
            address,
            {
                self.Column.COIN_ROW_ID: address.coin.rowId,
                self.Column.NAME: address.name
            },
            allow_hd_path=True)
        assert address.rowId > 0


class TxListTable(AbstractTable, name="transactions"):
    class Column(ColumnEnum):
        ROW_ID: Final = AbstractTable.Column.ROW_ID.value
        COIN_ROW_ID: Final = ColumnDefinition(
            "coin_row_id",
            "INTEGER NOT NULL")

        NAME: Final = ColumnDefinition(
            "name",
            "TEXT NOT NULL")
        HEIGHT: Final = ColumnDefinition(
            "height",
            "INTEGER NOT NULL")
        TIME: Final = ColumnDefinition(
            "time",
            "INTEGER NOT NULL")

        AMOUNT: Final = ColumnDefinition(
            "amount",
            "INTEGER NOT NULL")
        FEE_AMOUNT: Final = ColumnDefinition(
            "fee_amount",
            "INTEGER NOT NULL")

        IS_COINBASE: Final = ColumnDefinition(
            "is_coinbase",
            "INTEGER NOT NULL")

    _CONSTRAINT_LIST = (
        f"FOREIGN KEY ({_columnList(Column.COIN_ROW_ID)})"
        f" REFERENCES {CoinListTable.identifier}"
        f" ({_columnList(CoinListTable.Column.ROW_ID)})"
        f" ON DELETE CASCADE",
    )
    _UNIQUE_COLUMN_LIST = (
        (Column.COIN_ROW_ID, Column.NAME),
    )

    def _deserializeStatement(
            self,
            column_list: List[ColumnEnum],
            key_columns: Dict[Column, Any],
            *,
            address_row_id: int = -1,
            **options
    ) -> Tuple[str, List[Any]]:
        assert address_row_id > 0
        where, where_args = \
            self._database[AddressTxMapTable].statementSelectTransactions(
                address_row_id)
        return (
            (
                f"SELECT {_columnList(*column_list)}"
                f" FROM {self.identifier}"
                f" WHERE {_columnList(self.Column.ROW_ID)} IN ({where})"
            ),
            where_args
        )

    # TODO dynamic interface with coin.txList
    def deserializeAll(
            self,
            cursor: Cursor,
            address: Coin.Address) -> bool:
        assert address.coin.rowId > 0
        assert address.rowId > 0

        error = False
        for result in self._deserialize(
                cursor,
                address.coin.Tx,
                {
                    self.Column.COIN_ROW_ID: address.coin.rowId
                },
                {
                    self.Column.HEIGHT: Order.ASC,
                    self.Column.TIME: Order.ASC
                },
                address_row_id=address.rowId
        ):
            input_error, result["input_list"] = \
                self._database[TxIoListTable].deserializeAll(
                    cursor.connection.cursor(),
                    address.coin,
                    result["row_id"],
                    TxIoListTable.IoType.INPUT)
            output_error, result["output_list"] = \
                self._database[TxIoListTable].deserializeAll(
                    cursor.connection.cursor(),
                    address.coin,
                    result["row_id"],
                    TxIoListTable.IoType.OUTPUT)
            if input_error or output_error:
                error = True

            tx = address.coin.Tx.deserialize(result, address.coin)
            if tx is None:
                error = True
                self._database.logDeserializeError(address.coin.Tx, result)
            else:
                assert tx.rowId > 0
                address.appendTx(tx)
        return not error

    def serialize(
            self,
            cursor: Cursor,
            address: Optional[Coin.Address],
            tx: Coin.Tx) -> None:
        assert tx.coin.rowId > 0

        self._serialize(
            cursor,
            tx,
            {
                self.Column.COIN_ROW_ID: tx.coin.rowId,
                self.Column.NAME: tx.name
            })
        assert tx.rowId > 0

        # TODO delete old list?
        for io_type, io_list in (
                (TxIoListTable.IoType.INPUT, tx.inputList),
                (TxIoListTable.IoType.OUTPUT, tx.outputList)
        ):
            for io in io_list:
                self._database[TxIoListTable].serialize(
                    cursor,
                    tx,
                    io_type,
                    io)

        if address is not None:
            assert tx.coin.rowId == address.coin.rowId
            self._database[AddressTxMapTable].insert(
                    cursor,
                    address.rowId,
                    tx.rowId)


class TxIoListTable(AbstractTable, name="transactions_io"):
    class IoType(Enum):
        INPUT: Final = "input"
        OUTPUT: Final = "output"

    class Column(ColumnEnum):
        ROW_ID: Final = AbstractTable.Column.ROW_ID.value
        TX_ROW_ID: Final = ColumnDefinition(
            "transaction_row_id",
            "INTEGER NOT NULL")
        IO_TYPE: Final = ColumnDefinition(
            "io_type",
            "TEXT NOT NULL")  # IoType
        INDEX: Final = ColumnDefinition(
            "index",
            "INTEGER NOT NULL")

        OUTPUT_TYPE: Final = ColumnDefinition(
            "output_type",
            "TEXT NOT NULL")
        ADDRESS_NAME: Final = ColumnDefinition(
            "address_name",
            "TEXT")
        AMOUNT: Final = ColumnDefinition(
            "amount",
            "INTEGER NOT NULL")

    _CONSTRAINT_LIST = (
        f"FOREIGN KEY ({_columnList(Column.TX_ROW_ID)})"
        f" REFERENCES {TxListTable.identifier}"
        f" ({_columnList(TxListTable.Column.ROW_ID)})"
        f" ON DELETE CASCADE",
    )

    _UNIQUE_COLUMN_LIST = (
        (Column.TX_ROW_ID, Column.IO_TYPE, Column.INDEX),
    )

    def deserializeAll(
            self,
            cursor: Cursor,
            coin: Coin,
            tx_row_id: int,
            io_type: IoType) -> Tuple[bool, List[Coin.Tx.Io]]:
        assert coin.rowId > 0
        assert tx_row_id > 0
        io_list = []

        error = False
        for result in self._deserialize(
                cursor,
                coin.Tx.Io,
                {
                    self.Column.TX_ROW_ID: tx_row_id,
                    self.Column.IO_TYPE: io_type.value
                },
                {
                    self.Column.INDEX: Order.ASC
                }
        ):
            io = coin.Tx.Io.deserialize(result, coin)
            if io is None:
                error = True
                self._database.logDeserializeError(coin.Tx.Io, result)
            else:
                assert io.rowId > 0
                io_list.append(io)

        return not error, io_list

    def serialize(
            self,
            cursor: Cursor,
            tx: Coin.Tx,
            io_type: IoType,
            io: Coin.Tx.Io) -> None:
        assert tx.rowId > 0

        self._serialize(
            cursor,
            io,
            {
                self.Column.TX_ROW_ID: tx.rowId,
                self.Column.IO_TYPE: io_type.value,
                self.Column.INDEX: io.index
            })
        assert io.rowId > 0


class AddressTxMapTable(AbstractTable, name="address_transaction_map"):
    class Column(ColumnEnum):
        ROW_ID: Final = AbstractTable.Column.ROW_ID.value

        ADDRESS_ROW_ID: Final = ColumnDefinition(
            "address_row_id",
            "INTEGER NOT NULL")
        TX_ROW_ID: Final = ColumnDefinition(
            "tx_row_id",
            "INTEGER NOT NULL")

    _CONSTRAINT_LIST = (
        f"FOREIGN KEY ({_columnList(Column.ADDRESS_ROW_ID)})"
        f" REFERENCES {AddressListTable.identifier}"
        f" ({_columnList(AddressListTable.Column.ROW_ID)})"
        f" ON DELETE CASCADE",

        f"FOREIGN KEY ({_columnList(Column.TX_ROW_ID)})"
        f" REFERENCES {TxListTable.identifier}"
        f" ({_columnList(TxListTable.Column.ROW_ID)})"
        f" ON DELETE CASCADE",
    )

    _UNIQUE_COLUMN_LIST = (
        (Column.ADDRESS_ROW_ID, Column.TX_ROW_ID),
    )

    def insert(
            self, cursor: Cursor,
            address_row_id: int,
            tx_row_id: int) -> None:
        assert address_row_id > 0
        assert tx_row_id > 0
        columns = (
            self.Column.ADDRESS_ROW_ID,
            self.Column.TX_ROW_ID)
        cursor.execute(
            f"INSERT OR IGNORE INTO {self.identifier}"
            f" ({_columnList(*columns)})"
            f" VALUES({_qmarkList(len(columns))})",
            (address_row_id, tx_row_id))

    def statementSelectTransactions(
            self,
            address_row_id: int) -> Tuple[str, List[Any]]:
        assert address_row_id > 0
        return (
            (
                f"SELECT {_columnList(self.Column.TX_ROW_ID)}"
                f" FROM {self.identifier}"
                f" WHERE {_whereColumnList(self.Column.ADDRESS_ROW_ID)}"
            ),
            [address_row_id]
        )
