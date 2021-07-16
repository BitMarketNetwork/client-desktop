from __future__ import annotations

from typing import TYPE_CHECKING

import bmnsqlite3

from version import Product
from .tables import \
    AbstractTable, \
    AddressListTable, \
    CoinListTable, \
    MetadataTable, \
    TxIoListTable, \
    TxListTable
from .wrappers import Connection
from ..logger import Logger
from ..utils.class_property import classproperty

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Dict, Final, Optional, Type, Union
    from ..application import CoreApplication


class Database:
    _ENGINE = bmnsqlite3
    _VERSION: Final = 1

    # https://sqlite.org/pragma.html
    _PRAGMA_LIST: Final = (
        "automatic_index = OFF",
        "case_sensitive_like = OFF",
        "encoding = 'UTF-8'",
        "foreign_keys = ON",
        "main.journal_mode = DELETE",
        "temp_store = MEMORY",
    )

    _TABLE_TYPE_LIST: Final = (
        MetadataTable,
        CoinListTable,
        AddressListTable,
        TxListTable,
        TxIoListTable
    )

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
            self._ENGINE.__name__,
            self._ENGINE.version)
        self._logger.debug(
            "SQLite version: %s",
            self._ENGINE.sqlite_version)

        self.__connection: Optional[Database._ENGINE.Connection] = None
        self.__table_list: Dict[int, AbstractTable] = {}
        self.__in_context = False

    def __enter__(self) -> None:
        assert self.isOpen
        assert not self.__in_context
        self.__connection.__enter__()
        self.__in_context = True

    def __exit__(self, *args, **kwargs) -> None:
        assert self.isOpen
        assert self.__in_context
        self.__connection.__exit__(*args, **kwargs)
        self.__in_context = False

    def __getitem__(self, type_: Type[AbstractTable]) \
            -> Union[
                AbstractTable,
                MetadataTable
            ]:
        assert issubclass(type_, AbstractTable)
        table = self.__table_list.get(id(type_))
        if table is None:
            raise KeyError("table '{}' not found".format(type_.__name__))
        return table

    @classproperty
    def engine(self) -> Database._ENGINE:
        return self._ENGINE

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
            self._ENGINE.enable_callback_tracebacks(
                self._application.isDebugMode)
            self.__connection = self._ENGINE.connect(
                self._file_path,
                timeout=0,
                detect_types=0,
                isolation_level="DEFERRED",
                check_same_thread=True,
                factory=lambda *args, **kwargs: Connection(
                    *args,
                    logger=self._logger,
                    **kwargs),
                cached_statements=100,
                uri=False)  # noqa TODO type checking
        except (self._ENGINE.Error, self._ENGINE.Warning) as e:
            self.__connection = None
            self._logger.error("Failed to open database: %s", str(e))
            return False

        try:
            with self:
                for pragma in self._PRAGMA_LIST:
                    self.execute("PRAGMA " + pragma)
            with self:
                self._openTables()
        except (self._ENGINE.Error, self._ENGINE.Warning) as e:
            self._logger.error("Failed to prepare database tables: %s", str(e))
            self.close(force=True)
            return False

        return True

    def execute(self, query, *args) -> Database._ENGINE.Cursor:
        assert self.isOpen
        assert self.__in_context
        return self.__connection.execute(query, args)

    def close(self, *, force: bool = False) -> bool:
        if not self.isOpen:
            return True
        try:
            with self:
                self._closeTables()
            self.__connection.close()
        except (self._ENGINE.Warning, self._ENGINE.Error) as e:
            self._logger.error("Failed to close database: %s", str(e))
            if force:
                self.__connection = None
            return False
        self.__connection = None
        self._logger.debug("Database was closed successfully.")
        return True

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

    def _openTables(self) -> None:
        assert not self.__table_list
        for table_type in self._TABLE_TYPE_LIST:
            assert id(table_type) not in self.__table_list
            self.__table_list[id(table_type)] = table_type(self)

        version = self[MetadataTable].get(MetadataTable.Key.VERSION, int)
        if version is None or version == self._VERSION:
            upgrade = False
        elif version < self._VERSION:
            upgrade = True
        else:
            raise self._ENGINE.Warning(
                "existing database from a more recent version of the {}"
                " (existing database version {}, current database version {})"
                .format(
                    Product.NAME,
                    version,
                    self._VERSION))

        if upgrade:
            for table_type in self._TABLE_TYPE_LIST:
                self._logger.debug("Upgrading table '%s'...", table_type.name)
                self.__table_list[id(table_type)].upgrade(version)

        for table_type in self._TABLE_TYPE_LIST:
            self.__table_list[id(table_type)].open()

        self[MetadataTable].set(MetadataTable.Key.VERSION, self._VERSION)

    def _closeTables(self) -> None:
        for table_type in reversed(self._TABLE_TYPE_LIST):
            table = self.__table_list.get(id(table_type))
            if table is None:
                self._logger.debug(
                    "Can't close table '%s', it was not open.",
                    table_type.name)
                continue
            table.close()
        self.__table_list.clear()
