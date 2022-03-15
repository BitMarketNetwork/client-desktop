from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from .coin import CoinListTable
from .column import ColumnEnum
from .query import Query, SortOrder
from .table import AbstractTable

if TYPE_CHECKING:
    from typing import (
        Any,
        Dict,
        Final,
        List,
        Optional,
        Tuple)
    from . import Cursor
    from .column import Column
    from ..coins.abstract import Coin


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
