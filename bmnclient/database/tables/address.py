from __future__ import annotations

import glob
from typing import TYPE_CHECKING, Callable

from ...coins.hd import HdNode
from ...utils.class_property import classproperty
from .table import (
    Column,
    ColumnEnum,
    ColumnValue,
    SerializableRowList,
    SerializableTable,
)

if TYPE_CHECKING:
    from ...coins.abstract import Coin
    from .. import Cursor


class AddressesTable(SerializableTable, name="addresses"):
    class ColumnEnum(ColumnEnum):
        ROW_ID = ()
        COIN_ROW_ID = ("coin_row_id", "INTEGER NOT NULL")

        NAME = ("name", "TEXT NOT NULL")
        TYPE = ("type", "TEXT NOT NULL")
        BALANCE = ("balance", "INTEGER NOT NULL")
        TX_COUNT = ("tx_count", "INTEGER NOT NULL")

        LABEL = ("label", "TEXT NOT NULL")
        COMMENT = ("comment", "TEXT NOT NULL")
        KEY = ("key", "TEXT")
        IS_READ_ONLY = ("is_read_only", "INTEGER NOT NULL")

        HISTORY_FIRST_OFFSET = ("history_first_offset", "TEXT NOT NULL")
        HISTORY_LAST_OFFSET = ("history_last_offset", "TEXT NOT NULL")

    @classproperty
    def _CONSTRAINT_LIST(cls) -> Tuple[str, ...]:  # noqa
        from .coin import CoinsTable

        return (
            f"FOREIGN KEY ("
            f"{cls.ColumnEnum.COIN_ROW_ID})"
            f" REFERENCES {CoinsTable} ("
            f"{CoinsTable.ColumnEnum.ROW_ID})"
            f" ON DELETE CASCADE",
        )

    _UNIQUE_COLUMN_LIST = ((ColumnEnum.COIN_ROW_ID, ColumnEnum.NAME),)

    _KEY_COLUMN_LIST = (
        (
            ColumnEnum.COIN_ROW_ID,
            lambda o: o.coin.rowId if o.coin.rowId > 0 else None,
        ),
        (ColumnEnum.NAME, lambda o: o.name),
    )

    def upgrade(self, cursor: Cursor, old_version: int) -> None:
        # don't use identifiers from actual class!
        if old_version <= 1:
            self._upgrade_v1(cursor)

    @staticmethod
    def _upgrade_v1(cursor: Cursor) -> None:
        if cursor.isColumnExists("addresses", "amount"):
            cursor.execute(
                'ALTER TABLE "addresses" RENAME "amount" TO "balance"'
            )

    def rowList(
        self,
        coin: Coin,
        on_save_row: Callable[[int], None] | None = None,
        *,
        is_read_only: bool | None = None,
        with_utxo: bool | None = None,
    ) -> SerializableRowList[Coin.Address]:
        assert coin.rowId > 0

        where_expression = f"{self.ColumnEnum.COIN_ROW_ID} == ?"
        where_args = [coin.rowId]

        if is_read_only is not None:
            if is_read_only:
                where_expression += f" AND {self.ColumnEnum.IS_READ_ONLY} > 0"
            else:
                where_expression += f" AND {self.ColumnEnum.IS_READ_ONLY} <= 0"

        if with_utxo is not None:
            from .utxo import UtxosTable

            where_expression += (
                f" AND ("
                f"SELECT 1 FROM {UtxosTable}"
                f" WHERE"
                f" {UtxosTable}.{UtxosTable.ColumnEnum.ADDRESS_ROW_ID}"
                f" == {self}.{self.ColumnEnum.ROW_ID}"
                f" LIMIT 1"
                f") == ?"
            )
            where_args.append(1 if with_utxo else None)

        return SerializableRowList(
            type_=coin.Address,
            type_args=[coin],
            table=self,
            where_expression=where_expression,
            where_args=where_args,
            on_save_row=on_save_row,
        )

    def queryTotalBalance(self, coin: Coin) -> int:
        assert coin.rowId > 0
        with self._database.transaction() as c:
            c.execute(
                f"SELECT SUM({self.ColumnEnum.BALANCE})"
                f" FROM {self}"
                f" WHERE {self.ColumnEnum.COIN_ROW_ID} == ?"
                f" AND IFNULL({self.ColumnEnum.KEY}, ?) != ? ",
                [coin.rowId, "", ""],
            )
            value = c.fetchone()
        if value is None or value[0] is None:
            return 0
        return value[0]

    def queryLastHdIndex(self, coin: Coin, prefix: str) -> int:
        assert coin.rowId > 0
        prefix_length = len(prefix) + 1
        prefix = glob.escape(prefix) + "*"
        prefix = prefix.replace(
            HdNode.pathHardenedChars[0],
            "[" + "".join(HdNode.pathHardenedChars) + "]",
        )

        with self._database.transaction() as c:
            c.execute(
                f"SELECT MAX(CAST(SUBSTR("
                f"{self.ColumnEnum.KEY}, {prefix_length}) AS INTEGER))"
                f" FROM {self}"
                f" WHERE {self.ColumnEnum.COIN_ROW_ID} == ?"
                f" AND {self.ColumnEnum.KEY} GLOB ?",
                [coin.rowId, prefix],
            )
            value = c.fetchone()
        if value is None or value[0] is None:
            return -1
        return value[0]

    def queryName(self, coin: Coin, address_name: str) -> Coin.Address | None:
        assert coin.rowId > 0
        if not address_name:
            return None
        return self.loadSerializable(
            coin.Address,
            coin,
            key_columns=[
                ColumnValue(self.ColumnEnum.COIN_ROW_ID, coin.rowId),
                ColumnValue(self.ColumnEnum.NAME, address_name),
            ],
        )


class AddressTxsTable(SerializableTable, name="address_transactions"):
    class ColumnEnum(ColumnEnum):
        ROW_ID = ()

        ADDRESS_ROW_ID = (
            "address_row_id",
            "INTEGER NOT NULL",
            Column.Flags.ASSOCIATE_IS_PARENT,
        )
        TX_ROW_ID = (
            "tx_row_id",
            "INTEGER NOT NULL",
            Column.Flags.ASSOCIATE_IS_CHILD,
        )

    @classproperty
    def _CONSTRAINT_LIST(cls) -> tuple[str, ...]:  # noqa
        from .tx import TxsTable

        return (
            f"FOREIGN KEY ("
            f"{cls.ColumnEnum.ADDRESS_ROW_ID})"
            f" REFERENCES {AddressesTable} ("
            f"{AddressesTable.ColumnEnum.ROW_ID})"
            f" ON DELETE CASCADE",
            f"FOREIGN KEY ({cls.ColumnEnum.TX_ROW_ID})"
            f" REFERENCES {TxsTable} ("
            f"{TxsTable.ColumnEnum.ROW_ID})"
            f" ON DELETE CASCADE",
        )

    _UNIQUE_COLUMN_LIST = ((ColumnEnum.ADDRESS_ROW_ID, ColumnEnum.TX_ROW_ID),)

    def rowList(
        self,
        address: Coin.Address,
        on_save_row: Callable[[int], None] | None = None,
    ) -> SerializableRowList[Coin.Tx]:
        from .tx import TxsTable

        assert address.rowId > 0
        return SerializableRowList(
            type_=address.coin.Tx,
            type_args=[address.coin],
            table=self.database[TxsTable],
            where_expression=(
                f"{TxsTable.ColumnEnum.ROW_ID} IN ("
                f"SELECT {self.ColumnEnum.TX_ROW_ID}"
                f" FROM {self}"
                f" WHERE {self.ColumnEnum.ADDRESS_ROW_ID} == ?)"
            ),
            where_args=[address.rowId],
            on_save_row=on_save_row,
        )

    def associateSerializable(
        self, address: Coin.Address, tx: Coin.Tx
    ) -> SerializableTable.WriteResult:
        if not isinstance(tx, address.coin.Tx):
            return self.WriteResult()
        return super().associateSerializable(address, tx)
