from __future__ import annotations

from os import stat_result
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Property as QProperty
from PySide6.QtCore import QDateTime, QFileSystemWatcher
from PySide6.QtCore import Signal as QSignal
from PySide6.QtCore import Slot as QSlot

from ....logger import Logger
from . import AbstractStateModel
from .abstract import AbstractTableModel

if TYPE_CHECKING:
    from . import QmlApplication


class FileModel(AbstractStateModel):
    __stateChanged = QSignal()

    def __init__(
        self,
        application: QmlApplication,
        file: Path,
        *,
        logger: Logger | None = None,
        stat: stat_result | None = None,
    ) -> None:
        super().__init__(application)
        self._logger = logger
        self._file = file
        self._stat = stat
        if not self._stat:
            self._updateState()

    def __eq__(self, other: FileModel | Path) -> bool:
        if isinstance(other, self.__class__):
            other = other._file
        if isinstance(other, Path):
            return self._file == other
        return False

    def _updateState(self) -> bool:
        try:
            stat = self._file.stat()
        except OSError as exp:
            stat = None
            if self._logger:
                self._logger.error(
                    "Failed to stat file '%s'. %s",
                    self._file,
                    Logger.osErrorString(exp),
                )

        if self._stat == stat:
            return False

        self._stat = stat
        return True

    def update(self) -> None:
        if self._updateState():
            super().update()

    @property
    def model(self) -> FileModel:
        return self

    @property
    def file(self) -> Path:
        return self._file

    @property
    def stat(self) -> stat_result | None:
        return self._stat

    @QProperty(str, notify=__stateChanged)
    def name(self) -> str:
        return self._file.name

    @QProperty(str, notify=__stateChanged)
    def path(self) -> str:
        return str(self._file)

    @QProperty(int, notify=__stateChanged)
    def mtime(self) -> int:
        return int(self._stat.st_mtime) if self._stat else 0

    @QProperty(str, notify=__stateChanged)
    def mtimeHuman(self) -> str:
        value = QDateTime()
        value.setSecsSinceEpoch(self.mtime)
        return self.locale.toString(value, self.locale.FormatType.LongFormat)


class FileListModel(AbstractTableModel):
    def __init__(self, application: QmlApplication, path: Path) -> None:
        super().__init__(application, [])
        self._logger = Logger.classLogger(self.__class__)
        self._path = path
        self._watcher = QFileSystemWatcher(self)
        self._watcher.addPath(str(path))
        self._update()
        self._watcher.directoryChanged.connect(self._onDirectoryChanged)
        self._watcher.fileChanged.connect(self._onFileChanged)

    def _update(self) -> None:
        for file in self._application.walletsPath.iterdir():
            if file in self._source_list or not self._filter(file):
                continue
            self.lock(self.Lock.INSERT, -1, 1)
            self._source_list.append(
                FileModel(self._application, file, logger=self._logger)
            )
            self._watcher.addPath(str(file))
            self.unlock()

    def _filter(self, file: Path) -> bool:
        return file.is_file()

    @QSlot(str)
    def _onDirectoryChanged(self, path: str) -> None:
        self._update()

    @QSlot(str)
    def _onFileChanged(self, path: str) -> None:
        path = Path(path)
        if not path.is_file():
            try:
                index = self._source_list.index(path)
                self.lock(self.Lock.REMOVE, index, 1)
                del self._source_list[index]
                self.unlock()
            except ValueError:
                pass
        else:
            for file in self._source_list:
                if file == path:
                    file.update()
                    break
