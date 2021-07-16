from __future__ import annotations

import bmnsqlite3 as sql
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..application import CoreApplication


class Sqlite:
    COLUMN_NAMES = [
        "key",
        "value",
        "name",
        "visible",
        "address",
        "label",
        "message",
        "created",
        "coin_id",
        "type",
        "amount",
        "tx_count",
        "offset",
        "unverified_offset",
        "unverified_hash",
        "verified_height",
        "first_offset",
        "last_offset",
        "key",
        "height",
        "status",
        "time",
        "amount",
        "fee_amount",
        "address_id",
        "tx_id",
        "type",
        "output_type",
        "coinbase",
    ]
    TABLE_NAMES = [
        "meta",
        "coins",
        "private_keys",
        "coins",
        "addresses",
        "transactions",
        "inputs",
    ]

    def connect_impl(self, application: CoreApplication, db_name: str) -> None:
        self.__conn.text_factory = lambda v: v.decode()

    def exec(self, query: str, *args) -> None:
        if self.__conn is None:
            pass
        else:
            try:
                cursor = self.__conn.cursor()
                cursor.execute(query, *args)
                self.__conn.commit()
                return cursor
            except sql.OperationalError as oe:
                log.warning(f'SQL exception {oe} in {query}')
                raise oe from oe


    def __exec_script(self, query) -> None:
        try:
            cursor = self.__conn.cursor()
            cursor.executescript(query)
            self.__conn.commit()
            return cursor
        except sql.OperationalError as oe:
            log.fatal(f'SQL exception {oe} in {query}')
            sys.exit(1)

    def create_tables(self) -> None:
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.coins_table}
            (id INTEGER PRIMARY KEY ,
            {self.name_column}  TEXT NOT NULL UNIQUE,
            {self.visible_column}       INTEGER ,
            {self.height_column}        INTEGER ,
            {self.verified_height_column}        INTEGER,
            {self.offset_column}        TEXT,
            {self.unverified_offset_column}        TEXT,
            {self.unverified_hash_column}        TEXT
            );
        CREATE TABLE IF NOT EXISTS {self.addresses_table}
            (id INTEGER PRIMARY KEY,
            {self.address_column}   TEXT NOT NULL,
            {self.coin_id_column}   INTEGER NOT NULL,
            {self.label_column}     TEXT,
            {self.message_column}     TEXT,
            {self.created_column}     INTEGER NOT NULL,
            {self.type_column}      INTEGER NOT NULL,
            {self.amount_column}   INTEGER,
            {self.tx_count_column}  INTEGER,
            {self.first_offset_column}      TEXT,
            {self.last_offset_column}       TEXT,
            {self.key_column}       TEXT,
            FOREIGN KEY ({self.coin_id_column}) REFERENCES {self.coins_table} (id) ON DELETE CASCADE,
            UNIQUE({self.address_column}, {self.coin_id_column})
            );
        CREATE TABLE IF NOT EXISTS {self.transactions_table}
            (id INTEGER PRIMARY KEY,
            {self.name_column}   TEXT NOT NULL,
            {self.address_id_column} INTEGER NOT NULL,
            {self.height_column} INTEGER NOT NULL,
            {self.time_column}   INTEGER NOT NULL,
            {self.amount_column} INTEGER NOT NULL,
            {self.fee_amount_column}    INTEGER NOT NULL,
            {self.coinbase_column}    INTEGER NOT NULL,
            FOREIGN KEY ({self.address_id_column}) REFERENCES {self.addresses_table} (id) ON DELETE CASCADE,
            UNIQUE({self.name_column}, {self.address_id_column})
            );
        CREATE TABLE IF NOT EXISTS {self.inputs_table} (id INTEGER PRIMARY KEY,
            {self.address_column}   TEXT NOT NULL,
            {self.tx_id_column}     INTEGER NOT NULL,
            {self.amount_column}    INTEGER NOT NULL,
            {self.type_column}      INTEGER NOT NULL,
            {self.output_type_column}      TEXT NOT NULL,
            FOREIGN KEY ({self.tx_id_column}) REFERENCES {self.transactions_table} (id) ON DELETE CASCADE
            );
        """
        c = self.__exec_script(query)
        c.close()

    def __getattr__(self, attr: str) -> str:
        if attr.endswith("_column"):
            if attr[:-7] in self.COLUMN_NAMES:
                return attr[:-7]
        elif attr.endswith("_table"):
            if attr[:-6] in self.TABLE_NAMES:
                return attr[:-6]
        else:
            raise AttributeError(attr)
        raise AttributeError("bad table or column '{}'".format(attr))
