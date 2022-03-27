from __future__ import annotations

from typing import TYPE_CHECKING

from .table import AbstractSerializableTable, Column, ColumnEnum, RowListProxy
from ...utils.class_property import classproperty

if TYPE_CHECKING:
    from typing import Final, Optional, Tuple
    from ...coins.abstract import Coin


class TxIoListTable(AbstractSerializableTable, name="transactions_io"):
    class ColumnEnum(ColumnEnum):
        ROW_ID: Final = ()
        TX_ROW_ID: Final = ("transaction_row_id", "INTEGER NOT NULL")
        IO_TYPE: Final = ("io_type", "TEXT NOT NULL")  # Coin.Tx.Io.IoType
        INDEX: Final = ("index", "INTEGER NOT NULL")

        OUTPUT_TYPE: Final = ("output_type", "TEXT NOT NULL")
        ADDRESS: Final = ("address", "TEXT")
        AMOUNT: Final = ("amount", "INTEGER NOT NULL")

    @classproperty
    def _CONSTRAINT_LIST(cls) -> Tuple[str, ...]:  # noqa
        from .tx import TxListTable
        return (
            f"FOREIGN KEY ("
            f"{cls.ColumnEnum.TX_ROW_ID})"
            f" REFERENCES {TxListTable} ("
            f"{TxListTable.ColumnEnum.ROW_ID})"
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

    def rowListProxy(
            self,
            tx: Coin.Tx,
            io_type: Optional[Coin.Tx.Io.IoType]) -> Optional[RowListProxy]:
        if tx.rowId <= 0:
            return None
        where_columns = [self.ColumnEnum.TX_ROW_ID]
        where_args = [tx.rowId]
        if io_type is not None:
            where_columns.append(self.ColumnEnum.IO_TYPE)
            where_args.append(io_type.value)

        return RowListProxy(
            type_=tx.Io,
            type_args=[tx],
            table=self,
            where_expression=Column.joinWhere(where_columns),
            where_args=where_args)
