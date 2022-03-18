from __future__ import annotations

from typing import TYPE_CHECKING

from .table import AbstractTable, ColumnEnum, ColumnValue

if TYPE_CHECKING:
    from typing import Final
    from .. import Cursor
    from ...coins.abstract import Coin


class CoinListTable(AbstractTable, name="coins"):
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

    def deserialize(self, cursor: Cursor, coin: Coin) -> bool:
        result = next(
            self._deserialize(
                cursor,
                type(coin),
                {self.ColumnEnum.NAME: coin.name},
                limit=1,
                return_key_columns=True),
            None)
        if result is None:
            return False

        if not coin.deserializeUpdate(result):
            self._database.logDeserializeError(type(coin), result)
            return False
        else:
            assert coin.rowId > 0
            return True

    def serialize(self, cursor: Cursor, coin: Coin) -> None:
        self._serialize(
            cursor,
            coin,
            [ColumnValue(self.ColumnEnum.NAME, coin.name)])
        assert coin.rowId > 0
