from __future__ import annotations

from typing import TYPE_CHECKING

from .table import (
    AbstractSerializableTable,
    Column,
    ColumnEnum,
    ColumnValue,
    RowListProxy)
from ...utils.class_property import classproperty

if TYPE_CHECKING:
    from typing import Any, Final, List, Tuple


class AddressTxMapTable(
        AbstractSerializableTable,
        name="address_transaction_map"):
    class ColumnEnum(ColumnEnum):
        ROW_ID: Final = ()

        ADDRESS_ROW_ID: Final = ("address_row_id", "INTEGER NOT NULL")
        TX_ROW_ID: Final = ("tx_row_id", "INTEGER NOT NULL")

    @classproperty
    def _CONSTRAINT_LIST(cls) -> Tuple[str, ...]:  # noqa
        from .address import AddressListTable
        from .tx import TxListTable
        return (
            f"FOREIGN KEY ("
            f"{cls.ColumnEnum.ADDRESS_ROW_ID})"
            f" REFERENCES {AddressListTable} ("
            f"{AddressListTable.ColumnEnum.ROW_ID})"
            f" ON DELETE CASCADE",

            f"FOREIGN KEY ({cls.ColumnEnum.TX_ROW_ID})"
            f" REFERENCES {TxListTable} ("
            f"{TxListTable.ColumnEnum.ROW_ID})"
            f" ON DELETE CASCADE",
        )

    _UNIQUE_COLUMN_LIST = (
        (ColumnEnum.ADDRESS_ROW_ID, ColumnEnum.TX_ROW_ID),
    )

    def rowListProxy(self, *args, **kwargs) -> RowListProxy:
        raise NotImplementedError

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
            f"INSERT OR IGNORE INTO {self} ("
            f"{Column.join(columns)})"
            f" VALUES ({ColumnValue.join(len(columns))})",
            (address_row_id, tx_row_id))

    def statementSelectTransactions(
            self,
            address_row_id: int) -> Tuple[str, List[Any]]:
        assert address_row_id > 0
        return (
            (
                f"SELECT {self.ColumnEnum.TX_ROW_ID}"
                f" FROM {self}"
                f" WHERE {self.ColumnEnum.ADDRESS_ROW_ID} == ?"
            ),
            [address_row_id]
        )
