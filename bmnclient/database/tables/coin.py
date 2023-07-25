from __future__ import annotations

from .table import ColumnEnum, SerializableTable


class CoinsTable(SerializableTable, name="coins"):
    class ColumnEnum(ColumnEnum):
        ROW_ID = ()

        NAME = ("name", "TEXT NOT NULL UNIQUE")
        IS_ENABLED = ("is_enabled", "INTEGER NOT NULL")

        HEIGHT = ("height", "INTEGER NOT NULL")
        VERIFIED_HEIGHT = ("verified_height", "INTEGER NOT NULL")

        OFFSET = ("offset", "TEXT NOT NULL")
        UNVERIFIED_OFFSET = ("unverified_offset", "TEXT NOT NULL")
        UNVERIFIED_HASH = ("unverified_hash", "TEXT NOT NULL")

    _KEY_COLUMN_LIST = ((ColumnEnum.NAME, lambda o: o.name),)
