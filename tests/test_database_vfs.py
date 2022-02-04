from __future__ import annotations

import os
from itertools import chain
from unittest import TestCase

import bmnclient.database.vfs as vfs  # TODO kill
from bmnclient.database.vfs import VfsFile
from tests import TestApplication


class TestDatabaseVfs(TestCase):
    def test_sectors(self) -> None:
        for sector_size in chain(
                [i for i in range(16, 32)],  # AES block size as minimal value
                [512, 1024, 1025, 2049, 2048, 4096, 4105, 16383, 16384, 16385]
        ):
            self._test_sector(sector_size)

    def _test_sector(self, sector_size: int):
        TestApplication.tempPath.mkdir(parents=True, exist_ok=True)
        file = VfsFile(
            (
                TestApplication.tempPath
                / "sectors-{:06d}.dat".format(sector_size)
            ),
            vfs.SQLITE_OPEN_READWRITE
            | vfs.SQLITE_OPEN_CREATE
            | vfs.SQLITE_OPEN_MAIN_DB,
            sector_size)
        self.assertTrue(file.isEncrypted)
        self.assertTrue(file.isValid)
        self.assertEqual(sector_size, file.sectorSize)

        file.truncate(0)
        # noinspection PyProtectedMember
        os.lseek(file._fd, 0, os.SEEK_SET)

        # write sectors
        shadow = b""
        sector_count = 0xff + 1
        for i in range(sector_count):
            sector = (
                i.to_bytes(1, "little") +
                b"".join(
                    (i % (0xff + 1)).to_bytes(1, "little")
                    for i in range(file.sectorSize - 1)
                )
            )
            self.assertEqual(file.sectorSize, len(sector))
            file.write(sector, file.sectorSize * i)
            shadow += sector
        self.assertEqual(file.sectorSize * sector_count, len(shadow))
        self.assertEqual(file.file_size(), len(shadow))

        # read sectors: trim left
        for i in range(0, len(shadow) + 1, file.sectorSize // 2):
            self.assertEqual(
                shadow[i:],
                file.read(len(shadow) - i, i)
            )

        # read sectors: trim right
        for i in range(len(shadow), -1, -(file.sectorSize // 2)):
            self.assertEqual(
                shadow[0:i],
                file.read(i, 0)
            )

        # read sectors: sector boundaries
        for i in range(1, sector_count):
            offset = i * file.sectorSize - 1
            self.assertEqual(
                shadow[offset:offset + 2],
                file.read(2, offset)
            )
            chunk = file.read(2, offset)
            self.assertEqual(2, len(chunk))
            self.assertEqual(
                chunk[0],
                (file.sectorSize - 2) % (0xff + 1))
            self.assertEqual(chunk[1], i)

        # read sectors: half sector + full sector + half sector
        for i in range(1, sector_count):
            offset = i * file.sectorSize - file.sectorSize // 2
            size = (
                    file.sectorSize // 2 +
                    file.sectorSize +
                    file.sectorSize // 2
            )
            self.assertEqual(
                shadow[offset:offset + size],
                file.read(size, offset)
            )
            chunk = file.read(size, offset)
            self.assertEqual(chunk[file.sectorSize // 2], i)

        # write sectors: change single byte
        for i in range(0, sector_count):
            offset = i * file.sectorSize + 1
            file.write(b"#", offset)
            shadow = shadow[:offset] + b"#" + shadow[offset + 1:]
        for i in range(0, sector_count):
            offset = i * file.sectorSize
            data = file.read(3, offset)
            self.assertEqual(i, data[0])
            self.assertEqual(0x23, data[1])
            if file.sectorSize > 2:
                self.assertEqual(0x01, data[2])

        # write sectors: half sector + full sector + half sector
        for i in range(1, sector_count):
            offset = i * file.sectorSize - file.sectorSize // 2
            size = (
                    file.sectorSize // 2 +
                    file.sectorSize +
                    file.sectorSize // 2
            )
            chunk = (b"@" if i % 2 else b"*") * size
            file.write(chunk, offset)
            self.assertEqual(chunk, file.read(size, offset))
            shadow = (
                shadow[:offset]
                + chunk
                + shadow[offset + len(chunk):]
            )

        self.assertLessEqual(len(shadow), file.file_size())
        data = file.read(file.file_size(), 0)
        self.assertEqual(shadow, data[:len(shadow)])
        self.assertEqual(
            b"\0" * (file.file_size() - len(shadow)),
            data[len(shadow):])
