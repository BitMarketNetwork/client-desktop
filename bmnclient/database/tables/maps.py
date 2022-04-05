from __future__ import annotations

from .table import (
    AbstractSerializableTable,
    ColumnEnum,
    ColumnValue,
    ColumnValueType)
from ...utils.class_property import classproperty


class AddressTransactionsTable(
        AbstractSerializableTable,
        name="address_transactions"):
    class ColumnEnum(ColumnEnum):
        ROW_ID = ()

        ADDRESS_ROW_ID = ("address_row_id", "INTEGER NOT NULL")
        TX_ROW_ID = ("tx_row_id", "INTEGER NOT NULL")

    @classproperty
    def _CONSTRAINT_LIST(cls) -> tuple[str, ...]:  # noqa
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

    def associate(self, address_row_id: int, tx_row_id: int) -> bool:
        assert address_row_id > 0
        assert tx_row_id > 0
        return self.insert([
            ColumnValue(self.ColumnEnum.ADDRESS_ROW_ID, address_row_id),
            ColumnValue(self.ColumnEnum.TX_ROW_ID, tx_row_id)
        ]) > 0

    def filter(
            self,
            address_row_id: int) -> tuple[str, list[ColumnValueType]]:
        from .address import AddressListTable
        assert address_row_id > 0
        return (
            (
                f"{AddressListTable.ColumnEnum.ROW_ID} IN ("
                f"SELECT {self.ColumnEnum.TX_ROW_ID}"
                f" FROM {self}"
                f" WHERE {self.ColumnEnum.ADDRESS_ROW_ID} == ?)"
            ),
            [address_row_id]
        )
