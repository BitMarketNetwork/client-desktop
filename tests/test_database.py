from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from bmnclient.coins.list import CoinList
from bmnclient.database import Cursor, Database
from bmnclient.database.tables import (
    AbstractSerializableTable,
    AddressTransactionsTable,
    AddressesTable,
    CoinListTable,
    ColumnValue,
    MetadataTable,
    TxIoListTable,
    TxListTable)
from bmnclient.database.tables.table import ColumnEnum
from bmnclient.utils import Serializable, serializable
from tests.helpers import TestCaseApplication
from tests.test_coins import fillCoin

if TYPE_CHECKING:
    from typing import Any, List, Tuple
    from bmnclient.coins.abstract import Coin


class TestDatabase(TestCaseApplication):
    def _create(self, file_name: Path, *, mkdir: bool = True) -> Database:
        path = Path(self._application.tempPath / file_name)
        if mkdir:
            path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            path.unlink()
        return Database(self._application, path)

    def test_open(self) -> None:
        for i in range(0, 10):
            db = self._create(Path(str(i) + ".db"))

            self.assertFalse(db.filePath.exists())
            self.assertFalse(db.isOpen)
            self.assertTrue(db.open())
            self.assertTrue(db.isOpen)

            if i % 2 == 0:
                self.assertTrue(db.close())

            self.assertTrue(db.filePath.exists())
            self.assertTrue(db.remove())
            self.assertFalse(db.isOpen)
            self.assertFalse(db.filePath.exists())

        for i in range(0, 10):
            db = self._create(
                Path("not_exists") / (str(i) + ".db"),
                mkdir=False)
            self.assertFalse(db.filePath.exists())
            self.assertFalse(db.isOpen)
            self.assertFalse(db.open())
            self.assertFalse(db.isOpen)

            if i % 2 == 0:
                self.assertTrue(db.close())
            self.assertTrue(db.remove())
            self.assertFalse(db.isOpen)

    def test_transaction(self) -> None:
        db = self._create(Path("transaction.db"))
        self.assertTrue(db.open())

        with db.transaction(suppress_exceptions=False) as c1:
            self.assertIsNotNone(c1)

            with db.transaction(suppress_exceptions=True) as c2:
                self.assertIsNone(c2)

            ok = False
            try:
                with db.transaction(suppress_exceptions=False):
                    pass
            except db.Error:
                ok = True
            self.assertTrue(ok)

        with db.transaction(suppress_exceptions=False) as c1:
            self.assertIsNotNone(c1)
            with db.transaction(allow_in_transaction=True) as c2:
                self.assertIsNotNone(c2)

    def test_cursor(self) -> None:
        db = self._create(Path("cursor.db"))
        self.assertTrue(db.open())

        with db.transaction(suppress_exceptions=False) as cursor:
            self.assertTrue(cursor.isTableExists(MetadataTable))
            self.assertTrue(cursor.isTableExists(MetadataTable.name))
            self.assertFalse(cursor.isTableExists(MetadataTable.name + "__"))

            self.assertTrue(cursor.isColumnExists(MetadataTable, "key"))
            self.assertTrue(cursor.isColumnExists(MetadataTable, "value"))
            self.assertFalse(cursor.isColumnExists(MetadataTable, "key__"))
            self.assertFalse(cursor.isColumnExists(MetadataTable, "value__"))

            cursor.execute(f"DROP TABLE {MetadataTable}")
            self.assertFalse(cursor.isTableExists(MetadataTable))
            self.assertFalse(cursor.isTableExists(MetadataTable.name))
            self.assertFalse(cursor.isColumnExists(MetadataTable, "key"))
            self.assertFalse(cursor.isColumnExists(MetadataTable, "value"))

    def test_upgrade(self) -> None:
        db = self._create(Path("upgrade.db"))
        self.assertTrue(db.open())

        self.assertEqual(
            db.version,
            db[MetadataTable].get(MetadataTable.Key.VERSION, int))

        db[MetadataTable].set(MetadataTable.Key.VERSION, -1)
        self.assertEqual(
            -1,
            db[MetadataTable].get(MetadataTable.Key.VERSION, int))

        self.assertTrue(db.close())
        self.assertTrue(db.open())

        self.assertEqual(
            db.version,
            db[MetadataTable].get(MetadataTable.Key.VERSION, int))

        db[MetadataTable].set(MetadataTable.Key.VERSION, db.version + 1)

        self.assertTrue(db.close())
        self.assertFalse(db.open())

    def test_save(self) -> None:
        db = self._create(Path("save.db"))
        self.assertTrue(db.open())

        keys = [ColumnValue(MetadataTable.ColumnEnum.KEY, "key1")]
        data = (ColumnValue(MetadataTable.ColumnEnum.VALUE, "value1"), )

        row_id_1 = db[MetadataTable].save(-1, keys, data, fallback_search=True)
        self.assertLess(0, row_id_1)

        self.assertEqual(
            row_id_1,
            db[MetadataTable].save(-1, keys, data, fallback_search=True))
        self.assertEqual(
            row_id_1,
            db[MetadataTable].save(row_id_1, keys, data, fallback_search=True))
        self.assertEqual(
            row_id_1,
            db[MetadataTable].save(
                row_id_1 * 10000,
                keys,
                data,
                fallback_search=True))

        self.assertEqual(
            -1,
            db[MetadataTable].save(-1, keys, data, fallback_search=False))
        self.assertEqual(
            row_id_1,
            db[MetadataTable].save(row_id_1, keys, data, fallback_search=False))
        self.assertEqual(
            -1,
            db[MetadataTable].save(
                row_id_1 * 10000,
                keys,
                data,
                fallback_search=False))

    def test_load(self) -> None:
        db = self._create(Path("load.db"))
        self.assertTrue(db.open())

        keys = [ColumnValue(MetadataTable.ColumnEnum.KEY, "key1")]
        data = (ColumnValue(MetadataTable.ColumnEnum.VALUE, "value1"), )

        self.assertEqual(
            -1,
            db[MetadataTable].load(-1, keys, data, fallback_search=True))
        self.assertEqual(
            -1,
            db[MetadataTable].load(-1, keys, data, fallback_search=False))

        row_id_1 = db[MetadataTable].save(-1, keys, data)
        self.assertLess(0, row_id_1)

        ####

        for c in data:
            c.value = None
        self.assertEqual(
            row_id_1,
            db[MetadataTable].load(row_id_1, keys, data, fallback_search=True))
        for c in data:
            self.assertIsNotNone(c.value)

        for c in data:
            c.value = None
        self.assertEqual(
            row_id_1,
            db[MetadataTable].load(row_id_1, keys, data, fallback_search=False))
        for c in data:
            self.assertIsNotNone(c.value)

        ####

        for c in data:
            c.value = None
        self.assertEqual(
            row_id_1,
            db[MetadataTable].load(-1, keys, data, fallback_search=True))
        for c in data:
            self.assertIsNotNone(c.value)

        for c in data:
            c.value = None
        self.assertEqual(
            row_id_1,
            db[MetadataTable].load(-1, keys, data, fallback_search=False))
        for c in data:
            self.assertIsNotNone(c.value)

        ####

        for c in data:
            c.value = None
        self.assertEqual(
            row_id_1,
            db[MetadataTable].load(
                row_id_1 * 10000,
                keys,
                data,
                fallback_search=True))
        for c in data:
            self.assertIsNotNone(c.value)

        for c in data:
            c.value = None
        self.assertEqual(
            -1,
            db[MetadataTable].load(
                row_id_1 * 10000,
                keys,
                data,
                fallback_search=False))
        for c in data:
            self.assertIsNone(c.value)

    def test_serializable(self) -> None:
        # noinspection PyAbstractClass
        class Table(AbstractSerializableTable, name="table"):
            class ColumnEnum(ColumnEnum):
                ROW_ID = ()
                V1 = ("v1", "TEXT NOT NULL UNIQUE")
                V2 = ("v2", "TEXT NOT NULL")
                V3 = ("v3", "TEXT NOT NULL")
                V4 = ("v4", "TEXT NOT NULL")

        owner = self
        db = self._create(Path("serializable.db"))
        table = Table(db)

        class Object(Serializable):
            def __init__(self, *, row_id: int = -1, **kwargs) -> None:
                super().__init__(row_id=row_id)
                owner.assertGreaterEqual(4, len(kwargs))

                self._v1 = kwargs.get("v1", "1")

                self.result = table.completeSerializable(
                    self,
                    row_id,
                    (
                        [] if row_id > 0
                        else [ColumnValue(Table.ColumnEnum.V1, self.v1)]
                    ),
                    kwargs)

                self._v2 = kwargs.get("v2", "2")
                self._v3 = kwargs.get("v3", "3")
                self._v4 = kwargs.get("v4", "4")

            @serializable
            @property
            def v1(self) -> str:
                return self._v1

            @serializable
            @property
            def v2(self) -> str:
                return self._v2

            @v2.setter
            def v2(self, v: str) -> None:
                self._v2 = v

            @serializable
            @property
            def v3(self) -> str:
                return self._v3

            @v3.setter
            def v3(self, v: str) -> None:
                self._v3 = v

            @serializable
            @property
            def v4(self) -> str:
                return self._v4

            @v4.setter
            def v4(self, v: str) -> None:
                self._v4 = v

        self.assertTrue(db.open())
        with db.transaction() as c:
            c.execute(repr(table))

        o1 = Object(v1="100", v2="200", v3="300", v4="400")
        self.assertEqual(0, o1.result)
        o1_row_id = table.saveSerializable(o1, [])
        self.assertLess(0, o1_row_id)
        self.assertEqual(o1_row_id, o1.rowId)
        self.assertEqual(o1_row_id, table.saveSerializable(o1, []))

        o2 = table.loadSerializable(
            Object,
            [ColumnValue(Table.ColumnEnum.V1, o1.v1)])
        self.assertIsInstance(o2, Object)
        self.assertEqual(0, o2.result)
        self.assertEqual(o1.rowId, o2.rowId)
        self.assertEqual(o1.v1, o2.v1)
        self.assertEqual(o1.v2, o2.v2)
        self.assertEqual(o1.v3, o2.v3)
        self.assertEqual(o1.v4, o2.v4)

        o2.v2 *= 10
        self.assertIs(
            o2,
            table.loadSerializable(
                o2,
                [ColumnValue(Table.ColumnEnum.V1, o1.v1)]))
        self.assertEqual(0, o1.result)
        self.assertEqual(o1.v2, o2.v2)

        o3 = Object(v1=o1.v1)
        self.assertEqual(3, o3.result)
        self.assertEqual(o1.rowId, o3.rowId)
        self.assertEqual(o1.v1, o3.v1)
        self.assertEqual(o1.v2, o3.v2)
        self.assertEqual(o1.v3, o3.v3)
        self.assertEqual(o1.v4, o3.v4)

        o4 = Object(v1=o1.v1*100)
        self.assertEqual(-1, o4.result)
        self.assertEqual(-1, o4.rowId)

    def _fill_db(self, db: Database, coin_list: CoinList) -> None:
        for coin in coin_list:
            fillCoin(self, coin, address_count=10, tx_count=10)
            coin_id = db[CoinListTable].saveSerializable(
                coin,
                [],
                use_row_id=False)

            for address in list(coin.addressList):
                address_id = db[AddressesTable].saveSerializable(
                    address,
                    [
                        ColumnValue(
                            AddressesTable.ColumnEnum.COIN_ROW_ID,
                            coin_id),
                        ColumnValue(
                            AddressesTable.ColumnEnum.NAME,
                            address.name),
                    ],
                    use_row_id=False)

                for tx in address.txList:
                    tx_id = db[TxListTable].saveSerializable(
                        tx,
                        [
                            ColumnValue(
                                TxListTable.ColumnEnum.COIN_ROW_ID,
                                coin_id),
                            ColumnValue(
                                TxListTable.ColumnEnum.NAME,
                                tx.name),
                        ],
                        use_row_id=False)

                    db[AddressTransactionsTable].associate(address_id, tx_id)

                    for io_type, io_list in (
                            (TxIoListTable.IoType.INPUT, tx.inputList),
                            (TxIoListTable.IoType.OUTPUT, tx.outputList)
                    ):
                        for io in io_list:
                            db[TxIoListTable].saveSerializable(
                                io,
                                [
                                    ColumnValue(
                                        TxIoListTable.ColumnEnum.TX_ROW_ID,
                                        tx_id),
                                    ColumnValue(
                                        TxIoListTable.ColumnEnum.IO_TYPE,
                                        io_type.value),
                                    ColumnValue(
                                        TxIoListTable.ColumnEnum.INDEX,
                                        io.index)
                                ],
                                use_row_id=False)

    def _select_coin(
            self,
            cursor: Cursor,
            coin: Coin) -> List[Tuple[Any]]:
        cursor.execute(
            f"SELECT * FROM {CoinListTable}"
            f" WHERE {CoinListTable.ColumnEnum.NAME} == ?",
            [coin.name])
        r = cursor.fetchall()
        self.assertIsNotNone(r)
        return r

    def _select_addresses(
            self,
            cursor: Cursor,
            coin: Coin) -> List[Tuple[Any]]:
        cursor.execute(
            f"SELECT * FROM {AddressesTable}"
            f" WHERE {AddressesTable.ColumnEnum.COIN_ROW_ID} IN ("
            f"SELECT {CoinListTable.ColumnEnum.ROW_ID}"
            f" FROM {CoinListTable}"
            f" WHERE  {CoinListTable.ColumnEnum.NAME} == ?)",
            [coin.name])
        r = cursor.fetchall()
        self.assertIsNotNone(r)
        return r

    def _select_transactions(
            self,
            cursor: Cursor,
            coin: Coin) -> List[Tuple[Any]]:
        cursor.execute(
            f"SELECT * FROM {TxListTable}"
            f" WHERE {TxListTable.ColumnEnum.COIN_ROW_ID} IN ("
            f"SELECT {CoinListTable.ColumnEnum.ROW_ID}"
            f" FROM {CoinListTable}"
            f" WHERE  {CoinListTable.ColumnEnum.NAME} == ?)",
            [coin.name])
        r = cursor.fetchall()
        self.assertIsNotNone(r)
        return r

    def _select_transaction_io(
            self,
            cursor: Cursor,
            tx: Coin.Tx) -> List[Tuple[Any]]:
        cursor.execute(
            f"SELECT * FROM {TxIoListTable}"
            f" WHERE {TxIoListTable.ColumnEnum.TX_ROW_ID} IN ("
            f"SELECT {TxListTable.ColumnEnum.ROW_ID}"
            f" FROM {TxListTable}"
            f" WHERE {TxListTable.ColumnEnum.NAME} == ?)",
            [tx.name])
        r = cursor.fetchall()
        self.assertIsNotNone(r)
        return r

    def _select_transaction_address_map(
            self,
            cursor: Cursor,
            tx: Coin.Tx) -> List[Tuple[Any]]:
        cursor.execute(
            f"SELECT * FROM {AddressTransactionsTable}"
            f" WHERE {AddressTransactionsTable.ColumnEnum.TX_ROW_ID} IN ("
            f"SELECT {TxListTable.ColumnEnum.ROW_ID}"
            f" FROM {TxListTable}"
            f" WHERE {TxListTable.ColumnEnum.NAME} == ?)",
            [tx.name])
        r = cursor.fetchall()
        self.assertIsNotNone(r)
        return r

    def _select_address_transaction_map(
            self,
            cursor: Cursor,
            address: Coin.Address) -> List[Tuple[Any]]:
        cursor.execute(
            f"SELECT * FROM {AddressTransactionsTable}"
            f" WHERE {AddressTransactionsTable.ColumnEnum.ADDRESS_ROW_ID} IN ("
            f"SELECT {AddressesTable.ColumnEnum.ROW_ID}"
            f" FROM {AddressesTable}"
            f" WHERE {AddressesTable.ColumnEnum.NAME} == ?)",
            [address.name])
        r = cursor.fetchall()
        self.assertIsNotNone(r)
        return r

    def test_foreign_keys(self) -> None:
        db = self._create(Path("foreign_keys.db"))
        self.assertTrue(db.open())

        # generate
        coin_list = CoinList(model_factory=self._application.modelFactory)
        self._fill_db(db, coin_list)

        # check
        with db.transaction(suppress_exceptions=False) as c:
            for coin in coin_list:
                self.assertEqual(1, len(self._select_coin(c, coin)))
                self.assertEqual(10, len(self._select_addresses(c, coin)))
                self.assertEqual(100, len(self._select_transactions(c, coin)))

                self.assertEqual(10, len(coin.addressList))
                for address in coin.addressList:
                    self.assertEqual(10, len(address.txList))
                    self.assertEqual(
                        10,
                        len(self._select_address_transaction_map(c, address)))
                    for tx in address.txList:
                        self.assertEqual(
                            len(tx.inputList) + len(tx.outputList),
                            len(self._select_transaction_io(c, tx)))
                        self.assertEqual(
                            1,
                            len(self._select_transaction_address_map(c, tx)))

        # delete coin[0]
        with db.transaction(suppress_exceptions=False) as c:
            coin = coin_list[0]
            c.execute(
                f"DELETE FROM {CoinListTable} WHERE "
                f" {CoinListTable.ColumnEnum.ROW_ID} == ?",
                (coin.rowId, ))
            self.assertEqual(1, c.rowcount)
            self.assertEqual(0, len(self._select_coin(c, coin)))
            self.assertEqual(0, len(self._select_addresses(c, coin)))
            self.assertEqual(0, len(self._select_transactions(c, coin)))

            for address in coin.addressList:
                self.assertEqual(
                    0,
                    len(self._select_address_transaction_map(c, address)))
                for tx in address.txList:
                    self.assertEqual(
                        0,
                        len(self._select_transaction_io(c, tx)))
                    self.assertEqual(
                        0,
                        len(self._select_transaction_address_map(c, tx)))

        # delete coin[1].address[1]
        with db.transaction(suppress_exceptions=False) as c:
            address = coin_list[1].addressList[1]
            c.execute(
                f"DELETE FROM {AddressesTable}"
                f" WHERE {AddressesTable.ColumnEnum.NAME} == ?",
                [address.name])
            self.assertEqual(1, c.rowcount)
            self.assertEqual(
                0,
                len(self._select_address_transaction_map(c, address)))

        # delete coin[1].address[2].tx[2]
        with db.transaction(suppress_exceptions=False) as c:
            tx = coin_list[1].addressList[2].txList[2]
            c.execute(
                f"DELETE FROM {TxListTable}"
                f" WHERE {TxListTable.ColumnEnum.NAME} == ?",
                [tx.name])
            self.assertEqual(1, c.rowcount)
            self.assertEqual(
                0,
                len(self._select_transaction_io(c, tx)))
            self.assertEqual(
                0,
                len(self._select_transaction_address_map(c, tx)))
