from __future__ import annotations

import glob
from typing import TYPE_CHECKING

from .table import (
    AbstractSerializableTable,
    ColumnEnum,
    ColumnValue,
    ColumnValueType,
    RowListProxy)
from ...coins.hd import HdNode
from ...utils.class_property import classproperty

if TYPE_CHECKING:
    from .. import Cursor
    from ...coins.abstract import Coin


class AddressesTable(AbstractSerializableTable, name="addresses"):
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

        HISTORY_FIRST_OFFSET = ("history_first_offset", "TEXT NOT NULL")
        HISTORY_LAST_OFFSET = ("history_last_offset", "TEXT NOT NULL")

    @classproperty
    def _CONSTRAINT_LIST(cls) -> Tuple[str, ...]:  # noqa
        from .coin import CoinListTable
        return (
            f"FOREIGN KEY ("
            f"{cls.ColumnEnum.COIN_ROW_ID})"
            f" REFERENCES {CoinListTable} ("
            f"{CoinListTable.ColumnEnum.ROW_ID})"
            f" ON DELETE CASCADE",
        )

    _UNIQUE_COLUMN_LIST = (
        (ColumnEnum.COIN_ROW_ID, ColumnEnum.NAME),
    )

    _KEY_COLUMN_LIST = (
        (
            ColumnEnum.COIN_ROW_ID,
            lambda o: o.coin.rowId if o.coin.rowId > 0 else None
        ), (
            ColumnEnum.NAME,
            lambda o: o.name
        )
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

    def rowListProxy(self, coin: Coin) -> RowListProxy:
        assert coin.rowId > 0
        return RowListProxy(
            type_=coin.Address,
            type_args=[coin],
            table=self,
            where_expression=f"{self.ColumnEnum.COIN_ROW_ID} == ?",
            where_args=[coin.rowId])

    def queryTotalBalance(self, coin: Coin) -> int:
        assert coin.rowId > 0
        with self._database.transaction(allow_in_transaction=True) as c:
            c.execute(
                f"SELECT SUM({self.ColumnEnum.BALANCE})"
                f" FROM {self}"
                f" WHERE {self.ColumnEnum.COIN_ROW_ID} == ?"
                f" AND IFNULL({self.ColumnEnum.KEY}, ?) != ? ",
                [coin.rowId, "", ""])
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
            "[" + "".join(HdNode.pathHardenedChars) + "]")

        with self._database.transaction(allow_in_transaction=True) as c:
            c.execute(
                f"SELECT MAX(CAST(SUBSTR("
                f"{self.ColumnEnum.KEY}, {prefix_length}) AS INTEGER))"
                f" FROM {self}"
                f" WHERE {self.ColumnEnum.COIN_ROW_ID} == ?"
                f" AND {self.ColumnEnum.KEY} GLOB ?",
                [coin.rowId, prefix])
            value = c.fetchone()
        if value is None or value[0] is None:
            return -1
        return value[0]


class AddressTransactionsTable(
        AbstractSerializableTable,
        name="address_transactions"):
    class ColumnEnum(ColumnEnum):
        ROW_ID = ()

        ADDRESS_ROW_ID = ("address_row_id", "INTEGER NOT NULL")
        TX_ROW_ID = ("tx_row_id", "INTEGER NOT NULL")

    @classproperty
    def _CONSTRAINT_LIST(cls) -> tuple[str, ...]:  # noqa
        from .tx import TxListTable
        return (
            f"FOREIGN KEY ("
            f"{cls.ColumnEnum.ADDRESS_ROW_ID})"
            f" REFERENCES {AddressesTable} ("
            f"{AddressesTable.ColumnEnum.ROW_ID})"
            f" ON DELETE CASCADE",

            f"FOREIGN KEY ({cls.ColumnEnum.TX_ROW_ID})"
            f" REFERENCES {TxListTable} ("
            f"{TxListTable.ColumnEnum.ROW_ID})"
            f" ON DELETE CASCADE",
        )

    _UNIQUE_COLUMN_LIST = (
        (ColumnEnum.ADDRESS_ROW_ID, ColumnEnum.TX_ROW_ID),
    )

    def associate(self, address: Coin.Address, tx: Coin.Tx) -> bool:
        assert address.rowId > 0
        assert tx.rowId > 0
        return self.insert([
            ColumnValue(self.ColumnEnum.ADDRESS_ROW_ID, address.rowId),
            ColumnValue(self.ColumnEnum.TX_ROW_ID, tx.rowId)
        ]) > 0

    def filter(
            self,
            address: Coin.Address) -> tuple[str, list[ColumnValueType]]:
        assert address.rowId > 0
        return (
            (
                f"{AddressesTable.ColumnEnum.ROW_ID} IN ("
                f"SELECT {self.ColumnEnum.TX_ROW_ID}"
                f" FROM {self}"
                f" WHERE {self.ColumnEnum.ADDRESS_ROW_ID} == ?)"
            ),
            [address.rowId]
        )
