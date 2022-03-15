from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from .table import AbstractTable, ColumnEnum

if TYPE_CHECKING:
    from typing import Final, Optional, Type, Union
    from .. import Cursor


class MetadataTable(AbstractTable, name="metadata"):
    class ColumnEnum(ColumnEnum):
        ROW_ID: Final = ()
        KEY: Final = ("key", "TEXT NOT NULL UNIQUE")
        VALUE: Final = ("value", "TEXT")

    class Key(Enum):
        VERSION: Final = "version"

    def get(
            self,
            cursor: Cursor,
            key: Key,
            value_type: Type[Union[int, str]],
            default_value: Optional[int, str] = None) -> Optional[int, str]:
        try:
            cursor.execute(
                f"SELECT {self.joinColumns([self.ColumnEnum.VALUE])}"
                f" FROM {self.identifier}"
                f" WHERE {self.ColumnEnum.KEY.identifier} == ?"
                f" LIMIT 1",
                [key.value])
        except self._database.engine.OperationalError:
            value = default_value
        else:
            value = cursor.fetchone()
            value = value[0] if value is not None else default_value

        if value is None:
            return None

        try:
            return value_type(value)
        except (TypeError, ValueError):
            return default_value

    def set(self, cursor: Cursor, key: Key, value: Optional[int, str]) -> None:
        self._insertOrUpdate(
            cursor,
            [(self.ColumnEnum.KEY, key.value)],
            [(self.ColumnEnum.VALUE, str(value))],
            row_id_required=False)
