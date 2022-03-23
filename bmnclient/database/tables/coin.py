from __future__ import annotations

from typing import TYPE_CHECKING

from .table import AbstractSerializableTable, ColumnEnum, RowListProxy

if TYPE_CHECKING:
    from typing import Final


class CoinListTable(AbstractSerializableTable, name="coins"):
    class ColumnEnum(ColumnEnum):
        ROW_ID: Final = ()

        NAME: Final = (
            "name",
            "TEXT NOT NULL UNIQUE")
        IS_ENABLED: Final = (
            "is_enabled",
            "INTEGER NOT NULL")

        HEIGHT: Final = (
            "height",
            "INTEGER NOT NULL")
        VERIFIED_HEIGHT: Final = (
            "verified_height",
            "INTEGER NOT NULL")

        OFFSET: Final = (
            "offset",
            "TEXT NOT NULL")
        UNVERIFIED_OFFSET: Final = (
            "unverified_offset",
            "TEXT NOT NULL")
        UNVERIFIED_HASH: Final = (
            "unverified_hash",
            "TEXT NOT NULL")

    def rowListProxy(self, *args, **kwargs) -> RowListProxy:
        raise NotImplementedError
