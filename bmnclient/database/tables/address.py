from __future__ import annotations

import glob
from typing import TYPE_CHECKING

from .table import (
    AbstractSerializableTable,
    ColumnEnum,
    ColumnValue,
    RowListProxy)
from ...coins.hd import HdNode
from ...utils.class_property import classproperty

if TYPE_CHECKING:
    from typing import Final
    from .. import Cursor
    from ...coins.abstract import Coin


class AddressListTable(AbstractSerializableTable, name="addresses"):
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

    def upgrade(self, cursor: Cursor, old_version: int) -> None:
        # don't use identifiers from actual class!
        if old_version <= 1:
            self._upgrade_v1(cursor)

    @staticmethod
    def _upgrade_v1(cursor: Cursor) -> None:
        if cursor.isColumnExists("addresses", "amount"):
            cursor.execute(
                "ALTER TABLE \"addresses\" RENAME \"amount\" TO \"balance\"")

    def serialize(self, cursor: Cursor, address: Coin.Address) -> None:
        assert address.coin.rowId > 0
        assert not address.isNullData

        self._serialize(
            address,
            [
                ColumnValue(self.ColumnEnum.COIN_ROW_ID, address.coin.rowId),
                ColumnValue(self.ColumnEnum.NAME, address.name)
            ])
        assert address.rowId > 0

    def rowListProxy(self, coin: Coin) -> RowListProxy:
        return RowListProxy(
            type_=coin.Address,
            type_args=[coin],
            table=self,
            where_expression=f"{self.ColumnEnum.COIN_ROW_ID} == ?",
            where_args=[coin.rowId])

    def queryTotalBalance(self, coin: Coin) -> int:
        with self._database.transaction(allow_in_transaction=True) as c:
            c.execute(
                f"SELECT SUM({self.ColumnEnum.BALANCE})"
                f" FROM {self}"
                f" WHERE {self.ColumnEnum.COIN_ROW_ID} == ?"
                f" AND IFNULL({self.ColumnEnum.KEY}, ?) != ? ",
                [coin.rowId, "", ""])
            value = c.fetchone()
        return value[0] if value is not None else 0

    def queryLastHdIndex(self, coin: Coin, prefix: str) -> int:
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
