
import logging
from typing import Any
import threading
import sys
import sqlite3 as sql
from .. import meta
from . import cipher

log = logging.getLogger(__name__)


class Connection (sql.Connection):
    pass


class DummyCursor:
    def close(self) -> None:
        pass


class SqLite:
    """
    To encrypt sqlite we use hashing for names and aes for data
    but consider using native convertors
    * sqlite3.register_converter(typename, callable)
    * sqlite3.register_adapter(type, callable)
    """
    """
    TABLES:
        * meta
            - id , key , value
        * coins
            - id , name, visible, height , \
                offset, \
                unverified_offset, unverified_hash, verified_height \
                rate_usd
        * wallets
            # we keep both offsets otherwise we loose old tansactions in case user breaks servert tx chain
            - id , address, coin_id , label , message , created , type, balance , tx_count , \
                first_offset, last_offset, \
                key
        * transactions
            # status - detectable field
            - id , name , wallet_id , height , time , amount , fee , coin_base
        * inputs (outputs also here )
            - id , address , tx_id , amount , type ( 0 - input , 1 - output ), output_type
    """

    # i still need it.. it's hard to distinguish encoded columns
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
        "balance",
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
        "fee",
        "wallet_id",
        "tx_id",
        "type",
        "output_type",
        "rate_usd",
        "coin_base",
    ]
    TABLE_NAMES = [
        "meta",
        "coins",
        "private_keys",
        "coins",
        "wallets",
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
        real = "TEXT" if cipher.Cipher.ENCRYPT else "REAL"
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
            {self.unverified_hash_column}        TEXT,
            {self.rate_usd_column}      {real}
            );
        CREATE TABLE IF NOT EXISTS {self.wallets_table}
            (id INTEGER PRIMARY KEY,
            {self.address_column}   TEXT NOT NULL,
            {self.coin_id_column}   {integer} NOT NULL,
            {self.label_column}     TEXT,
            {self.message_column}     TEXT,
            {self.created_column}     {integer} NOT NULL,
            {self.type_column}      {integer} NOT NULL,
            {self.balance_column}   {integer},
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
            {self.wallet_id_column} {integer} NOT NULL,
            {self.height_column} {integer} NOT NULL,
            {self.time_column}   {integer} NOT NULL,
            {self.amount_column} {integer} NOT NULL,
            {self.fee_column}    {integer} NOT NULL,
            {self.coin_base_column}    {integer} NOT NULL,
            FOREIGN KEY ({self.wallet_id_column}) REFERENCES {self.wallets_table} (id) ON DELETE CASCADE,
            UNIQUE({self.name_column}, {self.wallet_id_column})
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
            return meta.setdefaultattr(
                self,
                name + "_title_",
                f"_{self.__proxy.make_hash(name)}",
            )
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
        raise AttributeError(f"Bad table or column: {attr}.")

    def __call__(self, data: Any, strong: bool = False, key: str = None):
        """
        key for debugging only!
        """
        if not self.__proxy:
            return "-"
        # if key:
            # log.debug(f"encrypt {key} strong:{strong}")
        return self.__proxy.encrypt(data, strong)

    def __pos__(self):
        pass

    def close(self) -> None:
        if self.__conn:
            self.__conn.close()
            log.debug('connection is closed ')
            self.__conn = None
