from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from ...utils.class_property import classproperty
from .table import ColumnEnum, SerializableRowList, SerializableTable

if TYPE_CHECKING:
    from ...coins.abstract import Coin


class TxsTable(SerializableTable, name="transactions"):
    class ColumnEnum(ColumnEnum):
        ROW_ID = ()
        COIN_ROW_ID = ("coin_row_id", "INTEGER NOT NULL")

        NAME = ("name", "TEXT NOT NULL")
        HEIGHT = ("height", "INTEGER NOT NULL")
        TIME = ("time", "INTEGER NOT NULL")

        AMOUNT = ("amount", "INTEGER NOT NULL")
        FEE_AMOUNT = ("fee_amount", "INTEGER NOT NULL")

        IS_COINBASE = ("is_coinbase", "INTEGER NOT NULL")

    @classproperty
    def _CONSTRAINT_LIST(cls) -> tuple[str, ...]:  # noqa
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

    def rowList(
        self, coin: Coin, on_save_row: Callable[[int], None] | None = None
    ) -> SerializableRowList[Coin.Tx]:
        assert coin.rowId > 0
        return SerializableRowList(
            type_=coin.Tx,
            type_args=[coin],
            table=self,
            where_expression=f"{self.ColumnEnum.COIN_ROW_ID} == ?",
            where_args=[coin.rowId],
            on_save_row=on_save_row,
        )
