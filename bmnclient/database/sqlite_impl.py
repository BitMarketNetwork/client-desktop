
import logging
from typing import Any
import threading
import sys
import sqlite3 as sql
from . import cipher

log = logging.getLogger(__name__)


class Connection (sql.Connection):
    pass


class DummyCursor:
    def close(self) -> None:
        pass


class SqLite:
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
    DEBUG = True

    def __init__(self):
        self.__mutex = threading.Lock()
        self.__conn = None
        self.__proxy = None

    def connect_impl(self, db_name: str) -> None:
        self.__proxy = cipher.Cipher()
        self.__conn = sql.connect(
            db_name,
            timeout=3,
            # detect_types=sql.PARSE_DECLTYPES,
            detect_types=sql.PARSE_COLNAMES,
            check_same_thread=True,
            cached_statements=100,
            # factory=Connection,
        )
        self.exec("PRAGMA foreign_keys=ON")
        sql.enable_callback_tracebacks(self.DEBUG)
        self.__conn.text_factory = self.__proxy.text_from

    def exec(self, query: str, *args) -> None:
        if self.__conn is None:
            return DummyCursor()
        else:
            try:
                cursor = self.__conn.cursor()
                cursor.execute(query, *args)
                self.__conn.commit()
                +self
                return cursor
            except sql.OperationalError as oe:
                log.warning(f'SQL exception {oe} in {query}')
                raise oe from oe


    def __exec_script(self, query) -> None:
        try:
            cursor = self.__conn.cursor()
            cursor.executescript(query)
            self.__conn.commit()
            +self
            return cursor
        except sql.OperationalError as oe:
            log.fatal(f'SQL exception {oe} in {query}')
            sys.exit(1)

    def __exec_many(self, query: str, *args) -> None:
        try:
            cursor = self.__conn.cursor()
            cursor.executemany(query, *args)
            self.__conn.commit()
            +self
            return cursor
        except sql.OperationalError as oe:
            log.fatal(f'SQL exception {oe} in {query}')
            sys.exit(1)

    def create_tables(self) -> None:
        integer = "TEXT" if cipher.Cipher.ENCRYPT else "INTEGER"
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.meta_table}
            (id INTEGER PRIMARY KEY,
            {self.key_column}   TEXT NOT NULL UNIQUE,
            {self.value_column} TEXT
            );
        CREATE TABLE IF NOT EXISTS {self.coins_table}
            (id INTEGER PRIMARY KEY ,
            {self.name_column}  TEXT NOT NULL UNIQUE,
            {self.visible_column}       {integer} ,
            {self.height_column}        {integer} ,
            {self.verified_height_column}        {integer},
            {self.offset_column}        TEXT,
            {self.unverified_offset_column}        TEXT,
            {self.unverified_hash_column}        TEXT
            );
        CREATE TABLE IF NOT EXISTS {self.addresses_table}
            (id INTEGER PRIMARY KEY,
            {self.address_column}   TEXT NOT NULL,
            {self.coin_id_column}   {integer} NOT NULL,
            {self.label_column}     TEXT,
            {self.message_column}     TEXT,
            {self.created_column}     {integer} NOT NULL,
            {self.type_column}      {integer} NOT NULL,
            {self.amount_column}   {integer},
            {self.tx_count_column}  {integer},
            {self.first_offset_column}      TEXT,
            {self.last_offset_column}       TEXT,
            {self.key_column}       TEXT,
            FOREIGN KEY ({self.coin_id_column}) REFERENCES {self.coins_table} (id) ON DELETE CASCADE,
            UNIQUE({self.address_column}, {self.coin_id_column})
            );
        CREATE TABLE IF NOT EXISTS {self.transactions_table}
            (id INTEGER PRIMARY KEY,
            {self.name_column}   TEXT NOT NULL,
            {self.address_id_column} {integer} NOT NULL,
            {self.height_column} {integer} NOT NULL,
            {self.time_column}   {integer} NOT NULL,
            {self.amount_column} {integer} NOT NULL,
            {self.fee_amount_column}    {integer} NOT NULL,
            {self.coinbase_column}    {integer} NOT NULL,
            FOREIGN KEY ({self.address_id_column}) REFERENCES {self.addresses_table} (id) ON DELETE CASCADE,
            UNIQUE({self.name_column}, {self.address_id_column})
            );
        CREATE TABLE IF NOT EXISTS {self.inputs_table} (id INTEGER PRIMARY KEY,
            {self.address_column}   TEXT NOT NULL,
            {self.tx_id_column}     {integer} NOT NULL,
            {self.amount_column}    {integer} NOT NULL,
            {self.type_column}      {integer} NOT NULL,
            {self.output_type_column}      TEXT NOT NULL,
            FOREIGN KEY ({self.tx_id_column}) REFERENCES {self.transactions_table} (id) ON DELETE CASCADE
            );
        """
        c = self.__exec_script(query)
        c.close()

    def test_table(self, table_name: str) -> bool:
        enc_table_name = self.__make_title(table_name)
        query = f'''
        SELECT name FROM sqlite_master WHERE name='{enc_table_name}';
        '''
        c = self._exec_(query)
        recs = c.fetchall()
        c.close()
        return recs is not None

    def __make_title(self, name: str) -> str:
        if cipher.Cipher.ENCRYPT:
            if not self.__proxy:
                return "-"
            name2 = name + "_title_"
            if not hasattr(self, name2):
                setattr(self, name2, f"_{self.__proxy.make_hash(name)}")
            return getattr(self, name2)
        return name

    def __getattr__(self, attr: str) -> str:
        if attr.endswith("_column"):
            if attr[:-7] in self.COLUMN_NAMES:
                return self.__make_title(attr[:-7])
        elif attr.endswith("_table"):
            if attr[:-6] in self.TABLE_NAMES:
                return self.__make_title(attr[:-6])
        else:
            raise AttributeError(attr)
        raise AttributeError("bad table or column \"{}\"".format(attr))

    def __call__(self, data: Any, strong: bool = False, key: str = None):
        if not self.__proxy:
            return "-"
        return self.__proxy.encrypt(data, strong)

    def __pos__(self):
        pass

    def close(self) -> None:
        if self.__conn:
            self.__conn.close()
            log.debug('connection is closed ')
            self.__conn = None
