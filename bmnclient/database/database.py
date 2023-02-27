from __future__ import annotations

from contextlib import contextmanager
from typing import ContextManager, Final, TYPE_CHECKING, TypeVar

import bmnsqlite3 as _engine

from .cursor import Cursor
from .tables import (
    AddressTxsTable,
    AddressesTable,
    CoinsTable,
    MetadataTable,
    Table,
    TxIosTable,
    TxsTable,
    UtxosTable)
from .vfs import Vfs
from ..debug import Debug
from ..logger import Logger
from ..utils.class_property import classproperty
from ..version import Product

if TYPE_CHECKING:
    from pathlib import Path
    from ..application import CoreApplication
    from ..utils import Serializable


class Connection(_engine.Connection):
    def __init__(self, *args, database: Database, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._database = database

    def cursor(self, factory=Cursor) -> Cursor:
        # TODO sqlite.Connection.cursor(factory)
        return super().cursor(
            factory=lambda *args, **kwargs: Cursor(
                *args,
                database=self._database,
                **kwargs)
        )


class Database:
    __initialized = False

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
        CoinsTable,
        AddressesTable,
        AddressTxsTable,
        TxsTable,
        TxIosTable,
        UtxosTable
    )

    class Error(_engine.OperationalError):
        def __init__(self, value: str, query: str | None = None):
            super().__init__(value)
            self._query = query

        @property
        def query(self) -> str | None:
            return self._query

    class SaveError(Error):
        pass

    class TransactionError(Error):
        pass

    class TransactionInEffectError(Error):
        def __init__(
                self,
                value: str = "transaction is already in effect",
                query: str | None = None):
            super().__init__(value, query)

    def __init__(self, application: CoreApplication, file_path: Path) -> None:
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

        self.__connection: _engine.Connection | None = None
        self.__table_list: dict[int, Table] = {}
        self.__in_transaction = 0  # TODO mutex?

    _TableT = TypeVar("_TableT", bound=Table)

    def __getitem__(self, type_: type(_TableT)) -> _TableT:
        assert issubclass(type_, Table)
        table = self.__table_list.get(id(type_))
        if table is None:
            raise KeyError("table '{}' not found".format(type_.name))
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

            if not self.__class__.__initialized:
                self.__class__.__initialized = True
                _engine.enable_callback_tracebacks(Debug.isEnabled)
                _engine.vfs_register(Vfs(self._application))  # TODO

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
            with self.transaction(allow_in_transaction=False) as cursor:
                for pragma in self._PRAGMA_LIST:
                    cursor.execute("PRAGMA " + pragma)
            with self.transaction(allow_in_transaction=False) as cursor:
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
            with self.transaction() as cursor:
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
            allow_in_transaction: bool = True,
            suppress_exceptions: bool = False
    ) -> ContextManager[Cursor | None]:
        if (
                not self.isOpen
                or (self.__in_transaction > 0 and not allow_in_transaction)
        ):
            if suppress_exceptions:
                try:
                    yield None
                finally:
                    pass
                return
            else:
                raise self.TransactionInEffectError

        self.__in_transaction += 1
        if self.__in_transaction == 1:
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
            assert self.isOpen and self.__in_transaction > 0
            cursor.close()

            if self.__in_transaction == 1:
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
                        self.__in_transaction -= 1
                        raise
            self.__in_transaction -= 1

    def logQuery(self, query: str) -> None:
        self._logger.debug("Query: %s", query)

    def logException(
            self,
            e: _engine.Error | _engine.Warning,
            query: str | None = None) -> None:
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
            type_: type(Serializable),
            result: dict[str, int | str]) -> None:
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

        if cursor.isTableExists(MetadataTable):
            version = self[MetadataTable].get(MetadataTable.Key.VERSION, int)
        else:
            version = None

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

        self[MetadataTable].set(MetadataTable.Key.VERSION, self._VERSION)

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
