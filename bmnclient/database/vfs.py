from __future__ import annotations

import os
from pathlib import PurePath
from typing import Final, TYPE_CHECKING

from ..crypto.cipher import BlockDeviceCipher
from ..logger import Logger
from ..version import Product

if TYPE_CHECKING:
    from ..application import CoreApplication


# TODO move to bmnsqlite3
SQLITE_OPEN_READONLY = 0x00000001
SQLITE_OPEN_READWRITE = 0x00000002
SQLITE_OPEN_CREATE = 0x00000004
SQLITE_OPEN_URI = 0x00000040
SQLITE_OPEN_MEMORY = 0x00000080

SQLITE_OPEN_NOMUTEX = 0x00008000
SQLITE_OPEN_FULLMUTEX = 0x00010000
SQLITE_OPEN_SHAREDCACHE = 0x00020000
SQLITE_OPEN_PRIVATECACHE = 0x00040000
SQLITE_OPEN_EXRESCODE = 0x02000000

SQLITE_OPEN_NOFOLLOW = 0x01000000
SQLITE_OPEN_DELETEONCLOSE = 0x00000008
SQLITE_OPEN_EXCLUSIVE = 0x00000010

SQLITE_OPEN_AUTOPROXY = 0x00000020

SQLITE_OPEN_MAIN_DB       = 0x00000100
SQLITE_OPEN_MAIN_JOURNAL  = 0x00000800
SQLITE_OPEN_TEMP_DB       = 0x00000200
SQLITE_OPEN_TEMP_JOURNAL  = 0x00001000
SQLITE_OPEN_TRANSIENT_DB  = 0x00000400
SQLITE_OPEN_SUBJOURNAL    = 0x00002000
SQLITE_OPEN_SUPER_JOURNAL = 0x00004000
SQLITE_OPEN_WAL           = 0x00080000


class VfsFile:
    _DEFAULT_OPEN_FLAGS: Final = (
            0
            | (os.O_BINARY if hasattr(os, "O_BINARY") else 0)
            | (os.O_CLOEXEC if hasattr(os, "O_CLOEXEC") else 0)
    )
    _DEFAULT_SECTOR_SIZE: Final = 4096

    def __init__(
            self,
            application: CoreApplication,
            file_name: str | PurePath,
            sqlite_flags: int,
            sector_size: int = 0) -> None:
        self._application = application
        self._file_path = PurePath(file_name)
        self._logger = Logger.classLogger(
            self.__class__,
            (None, self._file_path.name))

        flags = self._DEFAULT_OPEN_FLAGS

        if (sqlite_flags & SQLITE_OPEN_READONLY) == SQLITE_OPEN_READONLY:
            flags |= os.O_RDONLY
        if (sqlite_flags & SQLITE_OPEN_READWRITE) == SQLITE_OPEN_READWRITE:
            flags |= os.O_RDWR
        if (sqlite_flags & SQLITE_OPEN_CREATE) == SQLITE_OPEN_CREATE:
            flags |= os.O_CREAT
        if (sqlite_flags & SQLITE_OPEN_EXCLUSIVE) == SQLITE_OPEN_EXCLUSIVE:
            flags |= os.O_EXCL
        if (sqlite_flags & SQLITE_OPEN_NOFOLLOW) == SQLITE_OPEN_NOFOLLOW:
            flags |= os.O_NOFOLLOW

        # if (sqlite_flags & SQLITE_OPEN_URI) == SQLITE_OPEN_URI:
        #     raise NotImplementedError
        if (sqlite_flags & SQLITE_OPEN_MEMORY) == SQLITE_OPEN_MEMORY:
            raise NotImplementedError
        if (sqlite_flags & SQLITE_OPEN_AUTOPROXY) == SQLITE_OPEN_AUTOPROXY:
            raise NotImplementedError

        if (sqlite_flags & SQLITE_OPEN_DELETEONCLOSE) \
                == SQLITE_OPEN_DELETEONCLOSE:
            self._remove = True
        else:
            self._remove = False

        self._is_encrypted = False
        self._salt = b""
        for object_flag in (
                SQLITE_OPEN_MAIN_DB,
                SQLITE_OPEN_MAIN_JOURNAL,
                SQLITE_OPEN_TEMP_DB,
                SQLITE_OPEN_TEMP_JOURNAL,
                SQLITE_OPEN_TRANSIENT_DB,
                SQLITE_OPEN_SUBJOURNAL,
                SQLITE_OPEN_SUPER_JOURNAL,
                SQLITE_OPEN_WAL
        ):
            if (sqlite_flags & object_flag) == object_flag:
                self._is_encrypted = True
                self._salt = (
                        object_flag.to_bytes(4, "little")
                        + Product.SHORT_NAME.encode()
                        + b"\0" * (BlockDeviceCipher.saltSize - 4)
                )[:BlockDeviceCipher.saltSize]
                assert len(self._salt) == BlockDeviceCipher.saltSize
                break

        self._sector_size = \
            self._DEFAULT_SECTOR_SIZE if not sector_size else sector_size

        try:
            self._logger.debug(
                "Opening a file in '{}' mode."
                .format("ENCRYPTED" if self._is_encrypted else "PLAIN"))
            self._fd = os.open(self._file_path, flags, 0o644)  # TODO mode
        except OSError as e:
            self._fd = -1
            self._logger.error(
                "Failed to open file. %s",
                Logger.osErrorString(e))

    @property
    def isEncrypted(self) -> bool:
        return self._is_encrypted

    @property
    def sectorSize(self) -> int:
        return self._sector_size

    @property
    def isValid(self) -> bool:
        return self._fd >= 0

    def close(self) -> None:
        if not self.isValid:
            return
        try:
            os.close(self._fd)
        except OSError as e:
            self._logger.error(
                "Failed to close file. %s",
                Logger.osErrorString(e))
        self._fd = -1
        self._salt = b""

    def _ioChunks(
            self,
            size: int,
            offset: int,
            *,
            write_mode: bool) -> tuple[int, int]:
        sector_offset = (offset // self._sector_size) * self._sector_size
        chunk_offset = offset - sector_offset
        while size > 0:
            chunk_size = min(size, self._sector_size - chunk_offset)
            if write_mode and chunk_size == self._sector_size:
                # reading makes no sense...
                sector_data = b""
            else:
                os.lseek(self._fd, sector_offset, os.SEEK_SET)
                sector_data = os.read(self._fd, self._sector_size)
            if write_mode:
                os.lseek(self._fd, sector_offset, os.SEEK_SET)

            sector_index = sector_offset // self._sector_size
            yield sector_index, sector_data, chunk_offset, chunk_size

            size -= chunk_size
            sector_offset += self._sector_size
            chunk_offset = 0

    def _encrypt(self, sector_index: int, data: bytes) -> bytes:
        cipher = BlockDeviceCipher(
            BlockDeviceCipher.OpMode.ENCRYPT,
            self._application.keyStore.deriveBlockDeviceKey(),
            sector_index,
            self._salt)
        return cipher.update(data) + cipher.finalize()

    def _decrypt(self, sector_index: int, data: bytes) -> bytes:
        cipher = BlockDeviceCipher(
            BlockDeviceCipher.OpMode.DECRYPT,
            self._application.keyStore.deriveBlockDeviceKey(),
            sector_index,
            self._salt)
        return cipher.update(data) + cipher.finalize()

    def read(self, amount: int, offset: int) -> bytes:
        if not self.isValid:
            return b""
        try:
            if not self._is_encrypted:
                os.lseek(self._fd, offset, os.SEEK_SET)
                return os.read(self._fd, amount)

            result = []
            for sector_index, sector_data, chunk_offset, chunk_size \
                    in self._ioChunks(amount, offset, write_mode=False):
                if len(sector_data) != self._sector_size:
                    break
                sector_data = self._decrypt(sector_index, sector_data)
                if chunk_size == self._sector_size:
                    assert chunk_offset == 0
                    result.append(sector_data)
                else:
                    sector_data = memoryview(sector_data)
                    result.append(
                        sector_data[chunk_offset:chunk_offset + chunk_size])
            return b"".join(result)
        except OSError as e:
            self._logger.error(
                "Failed to read file (offset=%i, amount=%i). %s",
                offset,
                amount,
                Logger.osErrorString(e))
            return b""

    def write(self, data: bytes, offset: int) -> None:
        if not self.isValid:
            return
        try:
            if not self._is_encrypted:
                os.lseek(self._fd, offset, os.SEEK_SET)
                os.write(self._fd, data)
                return

            data_offset = 0
            for sector_index, sector_data, chunk_offset, chunk_size \
                    in self._ioChunks(len(data), offset, write_mode=True):
                if len(sector_data) == self._sector_size:
                    sector_data = self._decrypt(sector_index, sector_data)
                elif not len(sector_data):
                    sector_data = b"\0" * self._sector_size
                else:
                    self._logger.warning(
                        "Partial read of sector %i (offset %i), "
                        "data was ignored.",
                        sector_index,
                        sector_index * self.sectorSize)
                    sector_data = b"\0" * self._sector_size

                sector_data = (
                        sector_data[:chunk_offset]
                        + data[data_offset:data_offset + chunk_size]
                        + sector_data[chunk_offset + chunk_size:]
                )
                assert len(sector_data) == self._sector_size
                os.write(self._fd, self._encrypt(sector_index, sector_data))
                data_offset += chunk_size
        except OSError as e:
            self._logger.error(
                "Failed to write file (offset=%i, amount=%i). %s",
                offset,
                len(data),
                Logger.osErrorString(e))

    def truncate(self, size: int) -> int:
        if not self.isValid:
            return 0
        try:
            os.ftruncate(self._fd, size)
        except OSError as e:
            self._logger.error(
                "Failed to truncate file to size %i. %s",
                size,
                Logger.osErrorString(e))
        return 0

    def sync(self, flags: int) -> None:
        if not self.isValid:
            return
        try:
            os.fsync(self._fd)
        except OSError as e:
            self._logger.error(
                "Failed to sync file. %s",
                Logger.osErrorString(e))
        return None

    def file_size(self) -> int:
        if not self.isValid:
            return 0
        try:
            return os.fstat(self._fd).st_size
        except OSError as e:
            self._logger.error(
                "Failed to get size of file. %s",
                Logger.osErrorString(e))
        return 0

    def sector_size(self) -> int:
        return self._sector_size

    def device_characteristics(self) -> int:
        return 0x00000010  # TODO SQLITE_IOCAP_ATOMIC4K


class Vfs:
    def __init__(self, application: CoreApplication) -> None:
        self._application = application

    def open(self, file_name: str, sqlite_flags: int) -> VfsFile:
        return VfsFile(self._application, file_name, sqlite_flags)

    def close(self, vfs_file: VfsFile) -> None:
        vfs_file.close()

    def read(self, vfs_file: VfsFile, length: int, offset: int) -> bytes | bool:
        return vfs_file.read(length, offset)

    def write(self, vfs_file: VfsFile, data: bytes, offset: int) -> None:
        return vfs_file.write(data, offset)

    def truncate(self, vfs_file: VfsFile, size: int) -> int:
        return vfs_file.truncate(size)

    def sync(self, vfs_file: VfsFile, flags: int) -> None:
        return vfs_file.sync(flags)

    def file_size(self, vfs_file: VfsFile) -> int:
        return vfs_file.file_size()

    def sector_size(self, vfs_file: VfsFile) -> int:
        return vfs_file.sector_size()

    def device_characteristics(self, vfs_file: VfsFile) -> int:
        return vfs_file.device_characteristics()
