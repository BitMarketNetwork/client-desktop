from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from bmnclient.coins.list import CoinList
from bmnclient.database import Cursor, Database
from bmnclient.database.tables import (
    AddressListTable,
    AddressTxMapTable,
    CoinListTable,
    ColumnValue,
    MetadataTable,
    TxIoListTable,
    TxListTable)
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

        with db.transaction(suppress_exceptions=False) as c:
            version = db[MetadataTable].get(c, MetadataTable.Key.VERSION, int)
        self.assertEqual(db.version, version)

        with db.transaction(suppress_exceptions=False) as c:
            db[MetadataTable].set(c, MetadataTable.Key.VERSION, -1)
        with db.transaction(suppress_exceptions=False) as c:
            version = db[MetadataTable].get(c, MetadataTable.Key.VERSION, int)
        self.assertEqual(-1, version)

        self.assertTrue(db.close())
        self.assertTrue(db.open())

        with db.transaction(suppress_exceptions=False) as c:
            version = db[MetadataTable].get(c, MetadataTable.Key.VERSION, int)
        self.assertEqual(db.version, version)

        with db.transaction(suppress_exceptions=False) as c:
            db[MetadataTable].set(c, MetadataTable.Key.VERSION, db.version + 1)

        self.assertTrue(db.close())
        self.assertFalse(db.open())

    def test_save(self) -> None:
        db = self._create(Path("save.db"))
        self.assertTrue(db.open())

        keys = [ColumnValue(MetadataTable.ColumnEnum.KEY, "key1")]
        data = (ColumnValue(MetadataTable.ColumnEnum.VALUE, "value1"), )

        # noinspection PyProtectedMember
        logger = db._logger
        logger.debug("-" * 80)

        # INSERT: new row
        row_id_1 = db[MetadataTable].save(-1, keys, data)
        self.assertTrue(row_id_1 > 0)

        logger.debug("-" * 80)

        # INSERT + SELECT + UPDATE: row exists, only the key value is known,
        row_id_2 = db[MetadataTable].save(-1, keys, data)
        self.assertEqual(row_id_1, row_id_2)

        logger.debug("-" * 80)

        # UPDATE: row exists, row_id is known
        row_id_2 = db[MetadataTable].save(row_id_2, keys, data)
        self.assertEqual(row_id_1, row_id_2)

        logger.debug("-" * 80)

        # UPDATE + INSERT: invalid row_id
        keys = [ColumnValue(MetadataTable.ColumnEnum.KEY, "key2")]
        row_id_3 = db[MetadataTable].save(row_id_2 * 10000, keys, data)
        self.assertNotEqual(row_id_3, row_id_2 * 10000)
        self.assertLess(row_id_2, row_id_3)

        logger.debug("-" * 80)

        # UPDATE + INSERT + UPDATE: duplicated key and invalid row_id
        self.assertRaises(
            Database.SaveError,
            db[MetadataTable].save,
            row_id_3 * 10000,
            keys,
            data)

        logger.debug("-" * 80)

        # UPDATE: OK
        row_id_2 = db[MetadataTable].save(row_id_2, keys, data)
        self.assertEqual(row_id_1, row_id_2)

        logger.debug("-" * 80)

    def test_load(self) -> None:
        db = self._create(Path("load.db"))
        self.assertTrue(db.open())

        keys = [ColumnValue(MetadataTable.ColumnEnum.KEY, "key1")]
        data = (ColumnValue(MetadataTable.ColumnEnum.VALUE, "value1"), )

        # noinspection PyProtectedMember
        logger = db._logger
        logger.debug("-" * 80)

        row_id_1 = db[MetadataTable].load(-1, keys, data)
        self.assertEqual(-1, row_id_1)

        logger.debug("-" * 80)

        row_id_1 = db[MetadataTable].save(-1, keys, data)
        self.assertTrue(row_id_1 > 0)

        for c in data:
            c.value = None
        row_id_2 = db[MetadataTable].load(row_id_1, keys, data)
        self.assertEqual(row_id_1, row_id_2)
        for c in data:
            self.assertIsNotNone(c.value)

        logger.debug("-" * 80)

        for c in data:
            c.value = None
        row_id_2 = db[MetadataTable].load(-1, keys, data)
        self.assertEqual(row_id_1, row_id_2)
        for c in data:
            self.assertIsNotNone(c.value)

        logger.debug("-" * 80)

        for c in data:
            c.value = None
        row_id_2 = db[MetadataTable].load(row_id_1 * 10000, keys, data)
        self.assertEqual(row_id_1, row_id_2)
        for c in data:
            self.assertIsNotNone(c.value)

        logger.debug("-" * 80)

    def _fill_db(self, db: Database, coin_list: CoinList) -> None:
        for coin in coin_list:
            fillCoin(self, coin, address_count=10, tx_count=10)
            coin_id = db[CoinListTable].saveSerializable(
                coin,
                [],
                use_row_id=False)

            for address in list(coin.addressList):
                address_id = db[AddressListTable].saveSerializable(
                    address,
                    [
                        ColumnValue(
                            AddressListTable.ColumnEnum.COIN_ROW_ID,
                            coin_id),
                        ColumnValue(
                            AddressListTable.ColumnEnum.NAME,
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

                    db[AddressTxMapTable].associate(address_id, tx_id)

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
            f"SELECT * FROM {AddressListTable}"
            f" WHERE {AddressListTable.ColumnEnum.COIN_ROW_ID} IN ("
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
            f"SELECT * FROM {AddressTxMapTable}"
            f" WHERE {AddressTxMapTable.ColumnEnum.TX_ROW_ID} IN ("
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
            f"SELECT * FROM {AddressTxMapTable}"
            f" WHERE {AddressTxMapTable.ColumnEnum.ADDRESS_ROW_ID} IN ("
            f"SELECT {AddressListTable.ColumnEnum.ROW_ID}"
            f" FROM {AddressListTable}"
            f" WHERE {AddressListTable.ColumnEnum.NAME} == ?)",
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
                f"DELETE FROM {AddressListTable}"
                f" WHERE {AddressListTable.ColumnEnum.NAME} == ?",
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
