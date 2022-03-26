from __future__ import annotations

from typing import TYPE_CHECKING

from .table import AbstractSerializableTable, ColumnEnum, RowListProxy
from ...utils.class_property import classproperty

if TYPE_CHECKING:
    from typing import Final, Optional
    from ...coins.abstract import Coin


class UtxoListTable(AbstractSerializableTable, name="utxos"):
    class ColumnEnum(ColumnEnum):
        ROW_ID: Final = ()
        ADDRESS_ROW_ID: Final = ("address_row_id", "INTEGER NOT NULL")

        NAME: Final = ("name", "TEXT NOT NULL")
        INDEX: Final = ("index", "INTEGER NOT NULL")
        HEIGHT: Final = ("height", "INTEGER NOT NULL")
        AMOUNT: Final = ("amount", "INTEGER NOT NULL")

    @classproperty
    def _CONSTRAINT_LIST(cls) -> Tuple[str, ...]:  # noqa
        from .address import AddressListTable
        return (
            f"FOREIGN KEY ("
            f"{cls.ColumnEnum.ADDRESS_ROW_ID})"
            f" REFERENCES {AddressListTable} ("
            f"{AddressListTable.ColumnEnum.ROW_ID})"
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

    def rowListProxy(self, address: Coin.Address) -> Optional[RowListProxy]:
        if address.rowId <= 0:
            return None
        return RowListProxy(
            type_=address.coin.Tx.Utxo,
            type_args=[address],
            table=self,
            where_expression=f"{self.ColumnEnum.ADDRESS_ROW_ID} == ?",
            where_args=[address.rowId])
