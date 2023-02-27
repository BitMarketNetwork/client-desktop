from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from .table import (Column, ColumnEnum, SerializableRowList, SerializableTable)
from ...utils.class_property import classproperty

if TYPE_CHECKING:
    from ...coins.abstract import Coin


class TxIosTable(SerializableTable, name="transaction_ios"):
    class ColumnEnum(ColumnEnum):
        ROW_ID = ()
        TX_ROW_ID = ("transaction_row_id", "INTEGER NOT NULL")
        IO_TYPE = ("io_type", "TEXT NOT NULL")  # Coin.Tx.Io.IoType
        INDEX = ("index", "INTEGER NOT NULL")

        OUTPUT_TYPE = ("output_type", "TEXT NOT NULL")
        ADDRESS = ("address", "TEXT")
        AMOUNT = ("amount", "INTEGER NOT NULL")

    @classproperty
    def _CONSTRAINT_LIST(cls) -> tuple[str, ...]:  # noqa
        from .tx import TxsTable
        return (
            f"FOREIGN KEY ("
            f"{cls.ColumnEnum.TX_ROW_ID})"
            f" REFERENCES {TxsTable} ("
            f"{TxsTable.ColumnEnum.ROW_ID})"
            f" ON DELETE CASCADE",
        )

    _UNIQUE_COLUMN_LIST = (
        (ColumnEnum.TX_ROW_ID, ColumnEnum.IO_TYPE, ColumnEnum.INDEX),
    )

    _KEY_COLUMN_LIST = (
        (
            ColumnEnum.TX_ROW_ID,
            lambda o: o.tx.rowId if o.tx.rowId > 0 else None
        ), (
            ColumnEnum.IO_TYPE,
            lambda o: o.ioType.value
        ), (
            ColumnEnum.INDEX,
            lambda o: o.index
        )
    )

    def rowList(
            self,
            tx: Coin.Tx,
            io_type: Coin.Tx.Io.IoType | None,
            on_save_row: Callable[[int], None] | None = None
    ) -> SerializableRowList[Coin.Tx.Io]:
        assert tx.rowId > 0
        where_columns = [self.ColumnEnum.TX_ROW_ID]
        where_args = [tx.rowId]
        if io_type is not None:
            where_columns.append(self.ColumnEnum.IO_TYPE)
            where_args.append(io_type.value)
        return SerializableRowList(
            type_=tx.Io,
            type_args=[tx],
            table=self,
            where_expression=Column.joinWhere(where_columns),
            where_args=where_args,
            on_save_row=on_save_row)
