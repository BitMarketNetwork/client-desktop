from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from .table import AbstractTable, ColumnEnum, SortOrder
from ...utils.class_property import classproperty

if TYPE_CHECKING:
    from typing import Final, List, Tuple
    from .. import Cursor
    from ...coins.abstract import Coin


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

    @classproperty
    def _CONSTRAINT_LIST(cls) -> Tuple[str, ...]:  # noqa
        from .tx import TxListTable
        return (
            f"FOREIGN KEY ("
            f"{cls.joinColumns([cls.ColumnEnum.TX_ROW_ID])})"
            f" REFERENCES {TxListTable} ("
            f"{cls.joinColumns([TxListTable.ColumnEnum.ROW_ID])})"
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
