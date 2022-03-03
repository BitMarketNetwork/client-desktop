from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest import TestCase

from bmnclient.coins.list import CoinList
from bmnclient.database import Cursor, Database
from bmnclient.database.tables import (
    AddressListTable,
    AddressTxMapTable,
    CoinListTable,
    MetadataTable,
    TxIoListTable,
    TxListTable
)
from tests import TestApplication
from tests.test_coins import fillCoin

if TYPE_CHECKING:
    from typing import Any, List, Tuple
    from bmnclient.coins.abstract import Coin


class TestDatabase(TestCase):
    def setUp(self) -> None:
        self._application = TestApplication()
        self.assertTrue(self._application.keyStore.create("123456"))
        self.assertTrue(self._application.keyStore.open("123456"))

    def tearDown(self) -> None:
        self._application.setExitEvent()

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

    def test_insert_or_update(self) -> None:
        db = self._create(Path("insert_or_update.db"))
        self.assertTrue(db.open())

        keys = {
            MetadataTable.Column.KEY: "key1",
        }
        data = {
            MetadataTable.Column.VALUE: "value1"
        }

        with db.transaction(suppress_exceptions=False) as c:
            # noinspection PyProtectedMember
            db._logger.debug("-" * 80)

            # INSERT: new row
            # noinspection PyProtectedMember
            row_id_1 = db[MetadataTable]._insertOrUpdate(
                c,
                keys,
                data,
                row_id=-1,
                row_id_required=False
            )
            self.assertTrue(row_id_1 > 0)

            # noinspection PyProtectedMember
            db._logger.debug("-" * 80)

            # INSERT + UPDATE: row exists, only the key value is known
            # noinspection PyProtectedMember
            row_id_2 = db[MetadataTable]._insertOrUpdate(
                c,
                keys,
                data,
                row_id=-1,
                row_id_required=False
            )
            self.assertEqual(-1, row_id_2)

            # noinspection PyProtectedMember
            db._logger.debug("-" * 80)

            # INSERT + SELECT + UPDATE: row exists, only the key value is known,
            # row_id_required is True
            # noinspection PyProtectedMember
            row_id_3 = db[MetadataTable]._insertOrUpdate(
                c,
                keys,
                data,
                row_id=-1,
                row_id_required=True
            )
            self.assertEqual(row_id_1, row_id_3)

            # noinspection PyProtectedMember
            db._logger.debug("-" * 80)

            # UPDATE: row exists, row_id is known
            # noinspection PyProtectedMember
            row_id_3 = db[MetadataTable]._insertOrUpdate(
                c,
                keys,
                data,
                row_id=row_id_3,
                row_id_required=False
            )
            self.assertEqual(row_id_1, row_id_3)

            # noinspection PyProtectedMember
            db._logger.debug("-" * 80)

            # UPDATE: row exists, row_id is known, row_id_required doesn't
            # matter
            # noinspection PyProtectedMember
            row_id_3 = db[MetadataTable]._insertOrUpdate(
                c,
                keys,
                data,
                row_id=row_id_3,
                row_id_required=True
            )
            self.assertEqual(row_id_1, row_id_3)

            # noinspection PyProtectedMember
            db._logger.debug("-" * 80)

            # UPDATE + INSERT: invalid row_id
            keys[MetadataTable.Column.KEY] = "key2"
            # noinspection PyProtectedMember
            row_id_4 = db[MetadataTable]._insertOrUpdate(
                c,
                keys,
                data,
                row_id=row_id_3 * 10000,
                row_id_required=True
            )
            self.assertNotEqual(row_id_4, row_id_3 * 10000)
            self.assertLess(row_id_3, row_id_4)

            # noinspection PyProtectedMember
            db._logger.debug("-" * 80)

            # UPDATE + INSERT + UPDATE: duplicated key and invalid row_id
            # noinspection PyProtectedMember
            self.assertRaises(
                Database.engine.OperationalError,
                db[MetadataTable]._insertOrUpdate,
                c,
                keys,
                data,
                row_id=row_id_4 * 10000,
                row_id_required=True
            )

            # noinspection PyProtectedMember
            db._logger.debug("-" * 80)

            # UPDATE: OK
            # noinspection PyProtectedMember
            row_id_3 = db[MetadataTable]._insertOrUpdate(
                c,
                keys,
                data,
                row_id=row_id_3,
                row_id_required=True
            )
            self.assertEqual(row_id_1, row_id_3)

            # noinspection PyProtectedMember
            db._logger.debug("-" * 80)

    def _fill_db(
            self,
            db: Database,
            cursor: Cursor,
            coin_list: CoinList) -> None:
        for coin in coin_list:
            fillCoin(self, coin, address_count=10, tx_count=10)
            db[CoinListTable].serialize(cursor, coin)
            for address in coin.addressList:
                db[AddressListTable].serialize(cursor, address)
                for tx in address.txList:
                    db[TxListTable].serialize(cursor, address, tx)

    def _select_coin(
            self,
            cursor: Cursor,
            coin: Coin) -> List[Tuple[Any]]:
        cursor.execute(
            f"SELECT * FROM {CoinListTable.identifier} WHERE "
            f" {CoinListTable.Column.NAME.value.identifier} == ?",
            (coin.name,))
        r = cursor.fetchall()
        self.assertIsNotNone(r)
        return r

    def _select_addresses(
            self,
            cursor: Cursor,
            coin: Coin) -> List[Tuple[Any]]:
        cursor.execute(
            f"SELECT * FROM {AddressListTable.identifier} WHERE"
            f" {AddressListTable.Column.COIN_ROW_ID.value.identifier} == ?",
            (coin.rowId, ))
        r = cursor.fetchall()
        self.assertIsNotNone(r)
        return r

    def _select_transactions(
            self,
            cursor: Cursor,
            coin: Coin) -> List[Tuple[Any]]:
        cursor.execute(
            f"SELECT * FROM {TxListTable.identifier} WHERE"
            f" {TxListTable.Column.COIN_ROW_ID.value.identifier} == ?",
            (coin.rowId, ))
        r = cursor.fetchall()
        self.assertIsNotNone(r)
        return r

    def _select_transaction_io(
            self,
            cursor: Cursor,
            tx: Coin.Tx) -> List[Tuple[Any]]:
        cursor.execute(
            f"SELECT * FROM {TxIoListTable.identifier} WHERE"
            f" {TxIoListTable.Column.TX_ROW_ID.value.identifier} == ?",
            (tx.rowId, ))
        r = cursor.fetchall()
        self.assertIsNotNone(r)
        return r

    def _select_transaction_address_map(
            self,
            cursor: Cursor,
            tx: Coin.Tx) -> List[Tuple[Any]]:
        where = AddressTxMapTable.Column.TX_ROW_ID.value.identifier
        cursor.execute(
            f"SELECT * FROM {AddressTxMapTable.identifier} WHERE"
            f" {where} == ?",
            (tx.rowId, ))
        r = cursor.fetchall()
        self.assertIsNotNone(r)
        return r

    def _select_address_transaction_map(
            self,
            cursor: Cursor,
            address: Coin.Address) -> List[Tuple[Any]]:
        where = AddressTxMapTable.Column.ADDRESS_ROW_ID.value.identifier
        cursor.execute(
            f"SELECT * FROM {AddressTxMapTable.identifier}"
            f" WHERE {where} == ?",
            (address.rowId, ))
        r = cursor.fetchall()
        self.assertIsNotNone(r)
        return r

    def test_foreign_keys(self) -> None:
        db = self._create(Path("foreign_keys.db"))
        self.assertTrue(db.open())

        # generate
        coin_list = CoinList()
        with db.transaction(suppress_exceptions=False) as c:
            self._fill_db(db, c, coin_list)

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
                f"DELETE FROM {CoinListTable.identifier} WHERE "
                f" {CoinListTable.Column.ROW_ID.value.identifier} == ?",
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
                f"DELETE FROM {AddressListTable.identifier} WHERE "
                f" {AddressListTable.Column.ROW_ID.value.identifier} == ?",
                (address.rowId, ))
            self.assertEqual(1, c.rowcount)
            self.assertEqual(
                0,
                len(self._select_address_transaction_map(c, address)))

        # delete coin[1].address[2].tx[2]
        with db.transaction(suppress_exceptions=False) as c:
            tx = coin_list[1].addressList[2].txList[2]
            c.execute(
                f"DELETE FROM {TxListTable.identifier} WHERE "
                f" {TxListTable.Column.ROW_ID.value.identifier} == ?",
                (tx.rowId, ))
            self.assertEqual(1, c.rowcount)
            self.assertEqual(
                0,
                len(self._select_transaction_io(c, tx)))
            self.assertEqual(
                0,
                len(self._select_transaction_address_map(c, tx)))
