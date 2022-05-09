from __future__ import annotations

from typing import Callable, TYPE_CHECKING

from .table import ColumnEnum, SerializableRowList, SerializableTable
from ...utils.class_property import classproperty

if TYPE_CHECKING:
    from ...coins.abstract import Coin


class UtxosTable(SerializableTable, name="utxos"):
    class ColumnEnum(ColumnEnum):
        ROW_ID = ()
        ADDRESS_ROW_ID = ("address_row_id", "INTEGER NOT NULL")

        SCRIPT_TYPE = ("script_type", "TEXT NOT NULL")
        NAME = ("name", "TEXT NOT NULL")
        INDEX = ("index", "INTEGER NOT NULL")
        HEIGHT = ("height", "INTEGER NOT NULL")
        AMOUNT = ("amount", "INTEGER NOT NULL")

    @classproperty
    def _CONSTRAINT_LIST(cls) -> Tuple[str, ...]:  # noqa
        from .address import AddressesTable
        return (
            f"FOREIGN KEY ("
            f"{cls.ColumnEnum.ADDRESS_ROW_ID})"
            f" REFERENCES {AddressesTable} ("
            f"{AddressesTable.ColumnEnum.ROW_ID})"
            f" ON DELETE CASCADE",
        )

    _UNIQUE_COLUMN_LIST = (
        (ColumnEnum.ADDRESS_ROW_ID, ColumnEnum.NAME),
    )

    _KEY_COLUMN_LIST = (
        (
            ColumnEnum.ADDRESS_ROW_ID,
            lambda o: o.address.rowId if o.address.rowId > 0 else None
        ), (
            ColumnEnum.NAME,
            lambda o: o.name
        ),
    )

    def rowList(
            self,
            address: Coin.Address,
            on_save_row: Callable[[int], None] | None = None
    ) -> SerializableRowList[Coin.Tx.Utxo]:
        assert address.rowId > 0
        return SerializableRowList(
            type_=address.coin.Tx.Utxo,
            type_args=[address],
            table=self,
            where_expression=f"{self.ColumnEnum.ADDRESS_ROW_ID} == ?",
            where_args=[address.rowId],
            on_save_row=on_save_row)

    def queryTotalAmount(self, address: Coin.Address) -> int:
        assert address.rowId > 0
        with self._database.transaction(allow_in_transaction=True) as c:
            c.execute(
                f"SELECT SUM({self.ColumnEnum.AMOUNT})"
                f" FROM {self}"
                f" WHERE {self.ColumnEnum.ADDRESS_ROW_ID} == ?",
                [address.rowId])
            value = c.fetchone()
        if value is None or value[0] is None:
            return 0
        return value[0]
