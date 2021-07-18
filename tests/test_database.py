from pathlib import Path
from unittest import TestCase

from bmnclient.database import Database
from bmnclient.database.tables import MetadataTable
from tests import TestApplication


class TestDatabase(TestCase):
    def setUp(self) -> None:
        self._application = TestApplication(self)

    def tearDown(self) -> None:
        self._application.setExitEvent()

    def _create(self, file_name: Path, *, mkdir: bool = True) -> Database:
        path = Path(self._application.configPath / file_name)
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

    def test_upgrade(self) -> None:
        db = self._create(Path("upgrade.db"))
        self.assertTrue(db.open())

        with db:
            version = db[MetadataTable].get(MetadataTable.Key.VERSION, int)
        self.assertEqual(db.version, version)

        with db:
            self.assertTrue(
                db[MetadataTable].set(MetadataTable.Key.VERSION, -1))
        with db:
            version = db[MetadataTable].get(MetadataTable.Key.VERSION, int)
        self.assertEqual(-1, version)

        self.assertTrue(db.close())
        self.assertTrue(db.open())

        with db:
            version = db[MetadataTable].get(MetadataTable.Key.VERSION, int)
        self.assertEqual(db.version, version)

        with db:
            self.assertTrue(
                db[MetadataTable].set(
                    MetadataTable.Key.VERSION,
                    db.version + 1)
            )

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

        with db:
            # noinspection PyProtectedMember
            db._logger.debug("-" * 80)

            # INSERT: new row
            # noinspection PyProtectedMember
            row_id_1 = db[MetadataTable]._insertOrUpdate(
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
                db.engine.OperationalError,
                db[MetadataTable]._insertOrUpdate,
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
                keys,
                data,
                row_id=row_id_3,
                row_id_required=True
            )
            self.assertEqual(row_id_1, row_id_3)

            # noinspection PyProtectedMember
            db._logger.debug("-" * 80)
