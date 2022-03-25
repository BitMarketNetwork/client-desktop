from __future__ import annotations

from typing import TYPE_CHECKING

from .table import AbstractSerializableTable, ColumnEnum
from ...utils.class_property import classproperty

if TYPE_CHECKING:
    from typing import Final
    from .table import RowListProxy


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

    def rowListProxy(self, *args, **kwargs) -> RowListProxy:
        raise NotImplementedError
