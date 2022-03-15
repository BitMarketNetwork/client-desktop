# Rules:
# 1. Never raise new exceptions from *sqlite3.Error, *sqlite3.Warning or of a
#   subclasses thereof. Use only Database.Error.

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from ..debug import Debug

try:
    import bmnsqlite3 as _engine
except ImportError:
    import sqlite3 as _engine

from .metadata import MetadataTable
from .tables import (
    AbstractTable,
    AddressListTable,
    AddressTxMapTable,
    CoinListTable,
    TxIoListTable,
    TxListTable)
from .vfs import Vfs
from ..logger import Logger
from ..utils.class_property import classproperty
from ..version import Product

if TYPE_CHECKING:
    from pathlib import Path
    from typing import (
        Any,
        Callable,
        Dict,
        Final,
        Generator,
        Optional,
        Type,
        Union)
    from ..application import CoreApplication


class Cursor(_engine.Cursor):
    def __init__(self, *args, database: Database, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._database = database

    def execute(self, query, *args, **kwargs) -> Cursor:
        return self._execute(super().execute, query, *args, **kwargs)

    def executemany(self, query, *args, **kwargs) -> Cursor:
        return self._execute(super().executemany, query, *args, **kwargs)

    def executescript(self, query, *args, **kwargs) -> Cursor:
        return self._execute(super().executescript, query, *args, **kwargs)

    def _execute(self, origin: Callable, query, *args, **kwargs) -> Any:
        self._database.logQuery(query)
        try:
            cursor = origin(query, *args, **kwargs)
            assert cursor is self
            return cursor
        except (_engine.Error, _engine.Warning) as e:
            self._database.logException(e, query)
            raise

    def isTableExists(self, name: str) -> bool:
        r = self.execute(
            "SELECT COUNT(*) FROM \"sqlite_master\""
            " WHERE \"type\" == ? AND \"name\" == ?",
            ("table", name))
        return r.fetchone() is not None

    def isColumnExists(self, table_name: str, name: str) -> bool:
        if not self.isTableExists(table_name):
            return False
        for r in self.execute(f"PRAGMA table_info(\"{table_name}\")"):
            if len(r) > 2 and r[1] == name:
                return True
        return False


class Connection(_engine.Connection):
    def __init__(self, *args, database: Database, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._database = database

    def cursor(self, factory=Cursor) -> Cursor:
        # noinspection PyArgumentList
        # TODO sqlite.Connection.cursor(factory)
        return super().cursor(
            factory=lambda *args, **kwargs: Cursor(
                *args,
                database=self._database,
                **kwargs)
        )


class Database:
    _VERSION: Final = 2

    # https://sqlite.org/pragma.html
    _PRAGMA_LIST: Final = (
        "encoding = 'UTF-8'",
        "automatic_index = OFF",
        "case_sensitive_like = OFF",
        "foreign_keys = ON",
        "main.journal_mode = DELETE",
        "temp_store = MEMORY",
    )

    _TABLE_TYPE_LIST: Final = (
        MetadataTable,
        CoinListTable,
        AddressListTable,
        AddressTxMapTable,
        TxListTable,
        TxIoListTable
    )

    class Error(_engine.OperationalError):
        def __init__(self, value: str, query: Optional[str]):
            super().__init__(value)
            self._query = query

        @property
        def query(self) -> Optional[str]:
            return self._query

    class InsertOrUpdateError(Error):
        pass

    class TransactionError(Error):
        pass

    class TransactionInEffectError(Error):
        def __init__(
                self,
                value: str = "transaction is already in effect",
                query: Optional[str] = None):
            super().__init__(value, query)

    def __init__(
            self,
            application: CoreApplication,
            file_path: Path) -> None:
        self._application = application
        self._file_path = file_path

        self._logger = Logger.classLogger(
            self.__class__,
            (None, self._file_path.name))
        self._logger.debug(
            "%s version: %s",
            _engine.__name__,
            _engine.version)
        self._logger.debug(
            "SQLite version: %s",
            _engine.sqlite_version)

        self.__connection: Optional[_engine.Connection] = None
        self.__table_list: Dict[int, AbstractTable] = {}
        self.__in_transaction = False  # TODO mutex?

    def __getitem__(self, type_: Type[AbstractTable]) \
            -> Union[
                AbstractTable,
                AddressListTable,
                AddressTxMapTable,
                CoinListTable,
                MetadataTable,
                TxIoListTable,
                TxListTable
            ]:
        assert issubclass(type_, AbstractTable)
        table = self.__table_list.get(id(type_))
        if table is None:
            raise KeyError("table '{}' not found".format(type_.__name__))
        return table

    @classproperty
    def engine(self) -> _engine:
        return _engine

    @classproperty
    def version(cls) -> int:  # noqa
        return cls._VERSION

    @property
    def filePath(self) -> Path:
        return self._file_path

    @property
    def isOpen(self) -> bool:
        return self.__connection is not None

    def open(self) -> bool:
        assert not self.isOpen

        try:
            file_path = self._file_path.resolve(strict=False).as_uri()
            file_path += "?vfs=bmn_vfs"  # TODO
            _engine.vfs_register(Vfs(self._application))
            _engine.enable_callback_tracebacks(Debug.isEnabled)

            # noinspection PyTypeChecker
            # TODO PyTypeChecker:
            #  sqlite3.connect(factory: Type[Connection])
            #  bmnsqlite3.connect(uri)
            self.__connection = _engine.connect(
                file_path,
                timeout=0.0,
                detect_types=0,
                isolation_level="DEFERRED",
                check_same_thread=True,
                factory=lambda *args, **kwargs: Connection(
                    *args,
                    database=self,
                    **kwargs),
                cached_statements=100,
                uri=True)  # noqa
        except (_engine.Error, _engine.Warning, RuntimeError) as e:
            self.__connection = None
            self._logger.error("Failed to open database: %s", str(e))
            return False

        try:
            with self.transaction(suppress_exceptions=False) as cursor:
                for pragma in self._PRAGMA_LIST:
                    cursor.execute("PRAGMA " + pragma)
            with self.transaction(suppress_exceptions=False) as cursor:
                self._openTables(cursor)
        except (_engine.Error, _engine.Warning) as e:
            self._logger.error("Failed to prepare database tables: %s", str(e))
            self.close(force=True)
            return False

        return True

    def close(self, *, force: bool = False) -> bool:
        if not self.isOpen:
            return True
        try:
            with self.transaction(suppress_exceptions=False) as cursor:
                self._closeTables(cursor)
            self.__connection.close()
        except (_engine.Error, _engine.Warning) as e:
            self._logger.error("Failed to close database: %s", str(e))
            if force:
                self.__connection = None
            return False
        self.__connection = None
        self._logger.debug("Database was closed successfully.")
        return True

    @contextmanager
    def transaction(
            self,
            *,
            suppress_exceptions: bool = False
    ) -> Generator[Optional[Cursor], None, None]:
        if not self.isOpen or self.__in_transaction:
            if suppress_exceptions:
                try:
                    yield None
                finally:
                    pass
                return
            else:
                raise self.TransactionInEffectError

        self.__in_transaction = True
        self._logger.debug("BEGIN")
        cursor = self.__connection.cursor()
        commit = False

        try:
            yield cursor
            commit = True
        except self.Error as e:
            if suppress_exceptions:
                # not Cursor exception
                self.logException(e)
            else:
                raise
        except _engine.OperationalError:
            if suppress_exceptions:
                # logged with Cursor
                pass
            else:
                raise
        finally:
            assert self.isOpen and self.__in_transaction
            cursor.close()
            try:
                if commit:
                    self._logger.debug("COMMIT")
                    self.__connection.commit()
                else:
                    self._logger.debug("ROLLBACK")
                    self.__connection.rollback()
            except _engine.OperationalError as e:
                self._logger.error(
                    "Failed to %s transaction: %s",
                    "commit" if commit else "rollback",
                    str(e))
                if not suppress_exceptions:
                    raise

            self.__in_transaction = False

    def logQuery(self, query: str) -> None:
        self._logger.debug("Query: %s", query)

    def logException(
            self,
            e: Union[_engine.Error, _engine.Warning],
            query: Optional[str] = None) -> None:
        if not query and isinstance(e, self.Error):
            query = e.query

        message = (
            "Query failed with '%s' exception:\n\t%s\n\t%s",
            e.__class__.__name__,
            str(e),
            query if query else "NO STATEMENT")
        if isinstance(e, _engine.Warning):
            self._logger.warning(*message)
        else:
            self._logger.error(*message)

    def logDeserializeError(
            self,
            type_,
            result: Dict[str, Union[int, str]]) -> None:
        self._logger.error(
            "Failed to deserialize '%s' object.\n\t%s",
            str(type_.__name__),
            str(result))
        pass

    def remove(self) -> bool:
        if not self.close():
            return False
        if self._file_path.exists():
            try:
                self._file_path.unlink()
            except OSError as e:
                self._logger.error("Failed to remove database: %s", str(e))
                return False
        return True

    def _openTables(self, cursor: Cursor) -> None:
        assert not self.__table_list
        for table_type in self._TABLE_TYPE_LIST:
            assert id(table_type) not in self.__table_list
            self.__table_list[id(table_type)] = table_type(self)

        version = self[MetadataTable].get(
            cursor,
            MetadataTable.Key.VERSION,
            int)
        if version is None or version == self._VERSION:
            upgrade = False
        elif version < self._VERSION:
            upgrade = True
        else:
            raise self.Error(
                "existing database from a more recent version of the {}"
                " (existing database version {}, current database version {})"
                .format(
                    Product.NAME,
                    version,
                    self._VERSION),
                None)

        if upgrade:
            for table_type in self._TABLE_TYPE_LIST:
                self._logger.debug("Upgrading table '%s'...", table_type.name)
                self.__table_list[id(table_type)].upgrade(cursor, version)

        for table_type in self._TABLE_TYPE_LIST:
            self.__table_list[id(table_type)].open(cursor)

        self[MetadataTable].set(
            cursor,
            MetadataTable.Key.VERSION,
            self._VERSION)

    def _closeTables(self, cursor: Cursor) -> None:
        for table_type in reversed(self._TABLE_TYPE_LIST):
            table = self.__table_list.get(id(table_type))
            if table is None:
                self._logger.debug(
                    "Can't close table '%s', it was not open.",
                    table_type.name)
                continue
            table.close(cursor)
        self.__table_list.clear()
