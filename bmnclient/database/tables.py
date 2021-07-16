from __future__ import annotations

from enum import Enum
from itertools import chain
from typing import TYPE_CHECKING

from ..utils.class_property import classproperty

if TYPE_CHECKING:
    from .import Database
    from typing import Final, Optional, Tuple, Type, Union


class ColumnIdEnum(Enum):
    pass


class Column:
    __slots__ = ("_name", "_definition")

    def __init__(self, name: str, definition: str) -> None:
        self._name = name
        self._definition = definition

    def __str__(self) -> str:
        return self.id + " " + self._definition

    @property
    def name(self) -> str:
        return self._name

    @property
    def id(self) -> str:
        return "\"" + self._name + "\""

    @property
    def definition(self) -> str:
        return self._definition


class AbstractTable:
    _NAME = ""
    _CONSTRAINT_LIST: Tuple[str] = tuple()

    class ColumnId(ColumnIdEnum):
        ID: Final = Column("id", "INTEGER PRIMARY KEY")

    def __init__(self, database: Database) -> None:
        self._database = database

    def open(self) -> None:
        query = ", ".join(chain(
            (str(c.value) for c in self.ColumnId),
            (c for c in self._CONSTRAINT_LIST)))
        query = f"CREATE TABLE IF NOT EXISTS {self.id} ({query})"
        self._database.execute(query)

    def upgrade(self, old_version: int) -> None:
        pass

    def close(self) -> None:
        pass

    @classproperty
    def name(cls) -> str:  # noqa
        return cls._NAME

    @classproperty
    def id(cls) -> str:  # noqa
        return "\"" + cls._NAME + "\""


class MetadataTable(AbstractTable):
    _NAME = "metadata"

    class ColumnId(ColumnIdEnum):
        ID: Final = AbstractTable.ColumnId.ID.value
        KEY: Final = Column("key", "TEXT NOT NULL UNIQUE")
        VALUE: Final = Column("value", "TEXT")

    class Key(Enum):
        VERSION: Final = "version"

    def get(
            self,
            key: Key,
            value_type: Type[Union[int, str]],
            default_value: Optional[int, str] = None) -> Optional[int, str]:
        try:
            cursor = self._database.execute(
                f"SELECT {self.ColumnId.VALUE.value.id} FROM {self.id}"
                f" WHERE {self.ColumnId.KEY.value.id}==?",
                key.value
            )
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

    def set(self, key: Key, value: Optional[int, str]) -> bool:
        try:
            cursor = self._database.execute(
                f"INSERT OR REPLACE INTO {self.id} ("
                f"{self.ColumnId.KEY.value.id}, "
                f"{self.ColumnId.VALUE.value.id}) "
                "VALUES(?, ?)",
                key.value,
                str(value)
            )
        except self._database.engine.OperationalError:
            return False
        return cursor.lastrowid is not None


class CoinListTable(AbstractTable):
    _NAME = "coins"

    class ColumnId(ColumnIdEnum):
        ID: Final = AbstractTable.ColumnId.ID.value

        NAME: Final = Column("name", "TEXT NOT NULL UNIQUE")
        IS_ENABLED: Final = Column("is_enabled", "INTEGER NOT NULL")

        HEIGHT: Final = Column("height", "INTEGER NOT NULL")
        VERIFIED_HEIGHT: Final = Column("verified_height", "INTEGER NOT NULL")

        OFFSET: Final = Column("offset", "TEXT NOT NULL")
        UNVERIFIED_OFFSET: Final = Column("unverified_offset", "TEXT NOT NULL")
        UNVERIFIED_HASH: Final = Column("unverified_hash", "TEXT NOT NULL")


class AddressListTable(AbstractTable):
    _NAME = "addresses"

    class ColumnId(ColumnIdEnum):
        ID: Final = AbstractTable.ColumnId.ID.value
        COIN_ID: Final = Column("coin_id", "INTEGER NOT NULL")

        NAME: Final = Column("name", "TEXT NOT NULL")
        AMOUNT: Final = Column("amount", "INTEGER NOT NULL")
        TX_COUNT: Final = Column("tx_count", "INTEGER NOT NULL")

        LABEL: Final = Column("label", "TEXT NOT NULL")
        COMMENT: Final = Column("comment", "TEXT NOT NULL")
        KEY: Final = Column("key", "TEXT")

        HISTORY_FIRST_OFFSET: Final = Column(
            "history_first_offset",
            "TEXT NOT NULL")
        HISTORY_LAST_OFFSET: Final = Column(
            "history_last_offset",
            "TEXT NOT NULL")

    _CONSTRAINT_LIST = (
        f"FOREIGN KEY ({ColumnId.COIN_ID.value.id})"
        f" REFERENCES {CoinListTable.id} ({CoinListTable.ColumnId.ID.value.id})"
        f" ON DELETE CASCADE",

        f"UNIQUE({ColumnId.COIN_ID.value.id}, {ColumnId.NAME.value.id})",
    )


class TxListTable(AbstractTable):
    _NAME = "transactions"

    class ColumnId(ColumnIdEnum):
        ID: Final = AbstractTable.ColumnId.ID.value
        COIN_ID: Final = Column("coin_id", "INTEGER NOT NULL")

        NAME: Final = Column("name", "TEXT NOT NULL")
        HEIGHT: Final = Column("height", "INTEGER NOT NULL")
        TIME: Final = Column("time", "INTEGER NOT NULL")

        AMOUNT: Final = Column("amount", "INTEGER NOT NULL")
        FEE_AMOUNT: Final = Column("fee_amount", "INTEGER NOT NULL")

        IS_COINBASE: Final = Column("is_coinbase", "INTEGER NOT NULL")

    _CONSTRAINT_LIST = (
        f"FOREIGN KEY ({ColumnId.COIN_ID.value.id})"
        f" REFERENCES {CoinListTable.id} ({CoinListTable.ColumnId.ID.value.id})"
        f" ON DELETE CASCADE",

        f"UNIQUE({ColumnId.COIN_ID.value.id}, {ColumnId.NAME.value.id})",
    )


class TxIoListTable(AbstractTable):
    _NAME = "transactions_io"

    class ColumnId(ColumnIdEnum):
        ID: Final = AbstractTable.ColumnId.ID.value
        TX_ID: Final = Column("transaction_id", "INTEGER NOT NULL")
        IO_TYPE: Final = Column("io_type", "TEXT NOT NULL")  # input/output

        OUTPUT_TYPE: Final = Column("output_type", "TEXT NOT NULL")
        ADDRESS_NAME: Final = Column("address_name", "TEXT")
        AMOUNT: Final = Column("amount", "INTEGER NOT NULL")

    _CONSTRAINT_LIST = (
        f"FOREIGN KEY ({ColumnId.TX_ID.value.id})"
        f" REFERENCES {TxListTable.id} ({TxListTable.ColumnId.ID.value.id})"
        f" ON DELETE CASCADE",
    )
