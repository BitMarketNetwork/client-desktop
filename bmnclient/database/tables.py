from __future__ import annotations

from enum import Enum
from itertools import chain
from typing import TYPE_CHECKING

from .column import ColumnEnum
from .query import Query, SortOrder
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
        Sequence,
        Tuple,
        Type,
        Union)
    from . import Cursor, Database
    from .column import Column, ColumnValue
    from ..coins.abstract import Coin
    from ..utils.serialize import Serializable


class AbstractTable:
    class ColumnEnum(ColumnEnum):
        ROW_ID: Final = ()

    __NAME: str = ""
    __IDENTIFIER: str = ""
    _CONSTRAINT_LIST: Tuple[str] = tuple()
    _UNIQUE_COLUMN_LIST: Tuple[Tuple[Column]] = tuple()

    # noinspection PyMethodOverriding
    def __init_subclass__(cls, *args, name: str, **kwargs) -> None:
        super().__init_subclass__(*args, **kwargs)
        cls.__NAME = name
        cls.__IDENTIFIER = f"\"{cls.__NAME}\""

        definition_list = Query.join(chain(
            (str(c) for c in cls.ColumnEnum),
            (c for c in cls._CONSTRAINT_LIST),
            (
                f"UNIQUE({Query.joinColumns(c)})"
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
                f" SET {Query.joinColumnsQmark(c[0] for c in data_columns)}"
                f" WHERE {Query.joinColumnsQmark([self.ColumnEnum.ROW_ID])}",
                [*(c[1] for c in data_columns), row_id])
            if cursor.rowcount > 0:
                assert cursor.rowcount == 1
                return row_id

        cursor.execute(
            f"INSERT OR IGNORE INTO {self.identifier}"
            f" ({Query.joinColumns(c[0] for c in chain(key_columns, data_columns))})"
            f" VALUES({Query.qmark(len(key_columns) + len(data_columns))})",
            [c[1] for c in chain(key_columns, data_columns)])

        if cursor.rowcount > 0:
            assert cursor.rowcount == 1
            assert cursor.lastrowid > 0
            return cursor.lastrowid

        if row_id_required:
            if row_id <= 0:
                query = (
                    f"SELECT {Query.joinColumns([self.ColumnEnum.ROW_ID])}"
                    f" FROM {self.identifier}"
                    f" WHERE {Query.joinQmarkAnd(c[0] for c in key_columns)}"
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
            f" SET {Query.joinColumnsQmark(c[0] for c in data_columns)}"
            f" WHERE {Query.joinQmarkAnd(c[0] for c in key_columns)}"
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
            query += f" ORDER BY {Query.joinSortOrder(order_columns)}"

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
            **options
    ) -> Tuple[str, List[Any]]:
        return (
            (
                f"SELECT {Query.joinColumns(column_list)}"
                f" FROM {self.identifier}"
                f" WHERE {Query.joinQmarkAnd(key_columns.keys())}"
            ),
            [*key_columns.values()]
        )


class MetadataTable(AbstractTable, name="metadata"):
    class ColumnEnum(ColumnEnum):
        ROW_ID: Final = ()
        KEY: Final = ("key", "TEXT NOT NULL UNIQUE")
        VALUE: Final = ("value", "TEXT")

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
                f"SELECT {Query.joinColumns([self.ColumnEnum.VALUE])}"
                f" FROM {self.identifier}"
                f" WHERE {self.ColumnEnum.KEY.identifier} == ?"
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
            [(self.ColumnEnum.KEY, key.value)],
            [(self.ColumnEnum.VALUE, str(value))],
            row_id_required=False
        )


class CoinListTable(AbstractTable, name="coins"):
    class ColumnEnum(ColumnEnum):
        ROW_ID: Final = ()

        NAME: Final = (
            "name",
            "TEXT NOT NULL UNIQUE")
        IS_ENABLED: Final = (
            "is_enabled",
            "INTEGER NOT NULL")

        HEIGHT: Final = (
            "height",
            "INTEGER NOT NULL")
        VERIFIED_HEIGHT: Final = (
            "verified_height",
            "INTEGER NOT NULL")

        OFFSET: Final = (
            "offset",
            "TEXT NOT NULL")
        UNVERIFIED_OFFSET: Final = (
            "unverified_offset",
            "TEXT NOT NULL")
        UNVERIFIED_HASH: Final = (
            "unverified_hash",
            "TEXT NOT NULL")

    def deserialize(self, cursor: Cursor, coin: Coin) -> bool:
        result = next(
            self._deserialize(
                cursor,
                type(coin),
                {self.ColumnEnum.NAME: coin.name},
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
            [(self.ColumnEnum.NAME, coin.name)])
        assert coin.rowId > 0


class AddressListTable(AbstractTable, name="addresses"):
    class ColumnEnum(ColumnEnum):
        ROW_ID: Final = ()
        COIN_ROW_ID: Final = (
            "coin_row_id",
            "INTEGER NOT NULL")

        NAME: Final = (
            "name",
            "TEXT NOT NULL")
        TYPE: Final = (
            "type",
            "TEXT NOT NULL")
        BALANCE: Final = (
            "balance",
            "INTEGER NOT NULL")
        TX_COUNT: Final = (
            "tx_count",
            "INTEGER NOT NULL")

        LABEL: Final = (
            "label",
            "TEXT NOT NULL")
        COMMENT: Final = (
            "comment",
            "TEXT NOT NULL")
        KEY: Final = (
            "key",
            "TEXT")

        HISTORY_FIRST_OFFSET: Final = (
            "history_first_offset",
            "TEXT NOT NULL")
        HISTORY_LAST_OFFSET: Final = (
            "history_last_offset",
            "TEXT NOT NULL")

    _CONSTRAINT_LIST = (
        f"FOREIGN KEY ({Query.joinColumns([ColumnEnum.COIN_ROW_ID])})"
        f" REFERENCES {CoinListTable.identifier}"
        f" ({Query.joinColumns([CoinListTable.ColumnEnum.ROW_ID])})"
        f" ON DELETE CASCADE",
    )
    _UNIQUE_COLUMN_LIST = (
        (ColumnEnum.COIN_ROW_ID, ColumnEnum.NAME),
    )

    def upgrade(self, cursor: Cursor, old_version: int) -> None:
        # don't use identifiers from actual class!
        if old_version <= 1:
            self._upgrade_v1(cursor)

    @staticmethod
    def _upgrade_v1(cursor: Cursor) -> None:
        if cursor.isColumnExists("addresses", "amount"):
            cursor.execute(
                "ALTER TABLE \"addresses\" RENAME \"amount\" TO \"balance\"")

    # TODO dynamic interface with coin.txList, address.txList
    def deserializeAll(self, cursor: Cursor, coin: Coin) -> bool:
        assert coin.rowId > 0

        error = False
        for result in self._deserialize(
                cursor,
                coin.Address,
                {self.ColumnEnum.COIN_ROW_ID: coin.rowId}
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
            [
                (self.ColumnEnum.COIN_ROW_ID, address.coin.rowId),
                (self.ColumnEnum.NAME, address.name)
            ],
            allow_hd_path=True)
        assert address.rowId > 0


class TxListTable(AbstractTable, name="transactions"):
    class ColumnEnum(ColumnEnum):
        ROW_ID: Final = ()
        COIN_ROW_ID: Final = (
            "coin_row_id",
            "INTEGER NOT NULL")

        NAME: Final = (
            "name",
            "TEXT NOT NULL")
        HEIGHT: Final = (
            "height",
            "INTEGER NOT NULL")
        TIME: Final = (
            "time",
            "INTEGER NOT NULL")

        AMOUNT: Final = (
            "amount",
            "INTEGER NOT NULL")
        FEE_AMOUNT: Final = (
            "fee_amount",
            "INTEGER NOT NULL")

        IS_COINBASE: Final = (
            "is_coinbase",
            "INTEGER NOT NULL")

    _CONSTRAINT_LIST = (
        f"FOREIGN KEY ({Query.joinColumns([ColumnEnum.COIN_ROW_ID])})"
        f" REFERENCES {CoinListTable.identifier}"
        f" ({Query.joinColumns([CoinListTable.ColumnEnum.ROW_ID])})"
        f" ON DELETE CASCADE",
    )
    _UNIQUE_COLUMN_LIST = (
        (ColumnEnum.COIN_ROW_ID, ColumnEnum.NAME),
    )

    def _deserializeStatement(
            self,
            column_list: List[Column],
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
                f"SELECT {Query.joinColumns(column_list)}"
                f" FROM {self.identifier}"
                f" WHERE {Query.joinColumns([self.ColumnEnum.ROW_ID])}"
                f" IN ({where})"
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
                    self.ColumnEnum.COIN_ROW_ID: address.coin.rowId
                },
                (
                        (self.ColumnEnum.HEIGHT, SortOrder.ASC),
                        (self.ColumnEnum.TIME, SortOrder.ASC)
                ),
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
            [
                (self.ColumnEnum.COIN_ROW_ID, tx.coin.rowId),
                (self.ColumnEnum.NAME, tx.name)
            ])
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

    class ColumnEnum(ColumnEnum):
        ROW_ID: Final = ()
        TX_ROW_ID: Final = (
            "transaction_row_id",
            "INTEGER NOT NULL")
        IO_TYPE: Final = (
            "io_type",
            "TEXT NOT NULL")  # IoType
        INDEX: Final = (
            "index",
            "INTEGER NOT NULL")

        OUTPUT_TYPE: Final = (
            "output_type",
            "TEXT NOT NULL")
        ADDRESS_NAME: Final = (
            "address_name",
            "TEXT")
        AMOUNT: Final = (
            "amount",
            "INTEGER NOT NULL")

    _CONSTRAINT_LIST = (
        f"FOREIGN KEY ({Query.joinColumns([ColumnEnum.TX_ROW_ID])})"
        f" REFERENCES {TxListTable.identifier}"
        f" ({Query.joinColumns([TxListTable.ColumnEnum.ROW_ID])})"
        f" ON DELETE CASCADE",
    )

    _UNIQUE_COLUMN_LIST = (
        (ColumnEnum.TX_ROW_ID, ColumnEnum.IO_TYPE, ColumnEnum.INDEX),
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
                    self.ColumnEnum.TX_ROW_ID: tx_row_id,
                    self.ColumnEnum.IO_TYPE: io_type.value
                },
                (
                        (self.ColumnEnum.INDEX, SortOrder.ASC),
                )
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
            [
                (self.ColumnEnum.TX_ROW_ID, tx.rowId),
                (self.ColumnEnum.IO_TYPE, io_type.value),
                (self.ColumnEnum.INDEX, io.index)
            ])
        assert io.rowId > 0


class AddressTxMapTable(AbstractTable, name="address_transaction_map"):
    class ColumnEnum(ColumnEnum):
        ROW_ID: Final = ()

        ADDRESS_ROW_ID: Final = (
            "address_row_id",
            "INTEGER NOT NULL")
        TX_ROW_ID: Final = (
            "tx_row_id",
            "INTEGER NOT NULL")

    _CONSTRAINT_LIST = (
        f"FOREIGN KEY ({Query.joinColumns([ColumnEnum.ADDRESS_ROW_ID])})"
        f" REFERENCES {AddressListTable.identifier}"
        f" ({Query.joinColumns([AddressListTable.ColumnEnum.ROW_ID])})"
        f" ON DELETE CASCADE",

        f"FOREIGN KEY ({Query.joinColumns([ColumnEnum.TX_ROW_ID])})"
        f" REFERENCES {TxListTable.identifier}"
        f" ({Query.joinColumns([TxListTable.ColumnEnum.ROW_ID])})"
        f" ON DELETE CASCADE",
    )

    _UNIQUE_COLUMN_LIST = (
        (ColumnEnum.ADDRESS_ROW_ID, ColumnEnum.TX_ROW_ID),
    )

    def insert(
            self, cursor: Cursor,
            address_row_id: int,
            tx_row_id: int) -> None:
        assert address_row_id > 0
        assert tx_row_id > 0
        columns = (
            self.ColumnEnum.ADDRESS_ROW_ID,
            self.ColumnEnum.TX_ROW_ID)
        cursor.execute(
            f"INSERT OR IGNORE INTO {self.identifier}"
            f" ({Query.joinColumns(columns)})"
            f" VALUES({Query.qmark(len(columns))})",
            (address_row_id, tx_row_id))

    def statementSelectTransactions(
            self,
            address_row_id: int) -> Tuple[str, List[Any]]:
        assert address_row_id > 0
        return (
            (
                f"SELECT {Query.joinColumns([self.ColumnEnum.TX_ROW_ID])}"
                f" FROM {self.identifier}"
                f" WHERE {Query.joinQmarkAnd([self.ColumnEnum.ADDRESS_ROW_ID])}"
            ),
            [address_row_id]
        )
