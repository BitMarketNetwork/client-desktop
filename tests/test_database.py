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

    def test_open_1(self) -> None:
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
            db[MetadataTable].set(MetadataTable.Key.VERSION, -1)
        with db:
            version = db[MetadataTable].get(MetadataTable.Key.VERSION, int)
        self.assertEqual(-1, version)

        self.assertTrue(db.close())
        self.assertTrue(db.open())

        with db:
            version = db[MetadataTable].get(MetadataTable.Key.VERSION, int)
        self.assertEqual(db.version, version)

        with db:
            db[MetadataTable].set(MetadataTable.Key.VERSION, db.version + 1)

        self.assertTrue(db.close())
        self.assertFalse(db.open())
