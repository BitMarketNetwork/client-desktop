from __future__ import annotations

import json
from enum import Enum
from json.decoder import JSONDecodeError
from threading import RLock
from typing import TYPE_CHECKING

import pathvalidate

from .logger import Logger
from .utils import StaticList
from .version import Product, ProductPaths

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Final, Type, Union


class Config:
    class Key(Enum):
        pass

    def __init__(self, file_path: Path) -> None:
        self._logger = Logger.classLogger(
            self.__class__,
            (None, file_path.name),
        )
        self._file_path = file_path
        self._config = dict()
        self._lock = RLock()

    @property
    def filePath(self) -> Path:
        return self._file_path

    @filePath.setter
    def filePath(self, value: Path) -> None:
        self._file_path = value

    @property
    def lock(self) -> RLock:
        return self._lock

    @classmethod
    def isValidName(cls, name: str) -> bool:
        if name.lstrip() != name:
            return False
        return pathvalidate.is_valid_filename(
            name + ProductPaths.WALLET_SUFFIX,
            platform=pathvalidate.Platform.UNIVERSAL,
            min_len=1 + len(ProductPaths.WALLET_SUFFIX),
            max_len=127 - len(ProductPaths.WALLET_SUFFIX),
        )

    @classmethod
    def create(cls, path: Path, name: str) -> Config | None:
        logger = Logger.classLogger(cls)

        if not cls.isValidName(name):
            logger.error("Invalid characters found in name '%s'.", name)
            return None

        actual_name = name
        if path.exists():
            try:
                suffix = ProductPaths.WALLET_SUFFIX.lower()
                file_list = [
                    f.stem.lower()
                    for f in path.iterdir()
                    if f.suffix.lower() == suffix
                ]
            except OSError as exp:
                logger.error(
                    "Failed to list directory contents '%s'. %s",
                    path,
                    Logger.osErrorString(exp),
                )
                return None

            index = 0
            while actual_name.lower() in file_list:
                index += 1
                if index >= 10 * 1000:
                    logger.error(
                        "Too many duplicated files in directory '%s'.",
                        path,
                    )
                    return None
                actual_name = ProductPaths.WALLET_DUPLICATE_FORMAT.format(
                    name=name,
                    index=index,
                )

        config = cls(path / (actual_name + ProductPaths.WALLET_SUFFIX))
        return config if config.save() else None

    def load(self) -> bool:
        with self._lock:
            try:
                with open(
                    self._file_path,
                    mode="rt",
                    encoding=Product.ENCODING,
                    errors="strict",
                ) as file:
                    self._config = json.load(file)
                self._updateVersion()
                return True
            except FileNotFoundError:
                error_message = None
            except OSError as e:
                error_message = Logger.osErrorString(e)
            except JSONDecodeError as e:
                error_message = Logger.jsonDecodeErrorString(e)
            except ValueError as e:
                error_message = Logger.exceptionString(e)

            if error_message:
                self._logger.warning(
                    "Failed to read file '%s'. %s",
                    self._file_path,
                    str(error_message),
                )
            self._config = dict()
            self._updateVersion()
        return False

    def save(self) -> bool:
        with self._lock:
            try:
                self._file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(
                    self._file_path,
                    mode="w+t",
                    encoding=Product.ENCODING,
                    errors="strict",
                ) as file:
                    json.dump(
                        self._config,
                        file,
                        skipkeys=False,
                        indent=4,
                        sort_keys=True,
                    )
                    file.flush()
                return True
            except OSError as e:
                error_message = Logger.osErrorString(e)
            except ValueError as e:
                error_message = Logger.exceptionString(e)
            self._logger.warning(
                "Failed to write file '%s'. %s",
                self._file_path,
                str(error_message),
            )
        return False

    def get(
        self,
        key: Key,
        value_type: Type = str,
        default_value: ... = None,
    ) -> ...:
        key_list = key.value.split(".")
        with self._lock:
            current_config = self._config
            for i in range(len(key_list)):
                current_value = current_config.get(key_list[i])
                if (i + 1) == len(key_list):
                    if type(current_value) == value_type:
                        return current_value
                    else:
                        break
                if type(current_value) is not dict:
                    break
                current_config = current_value
        return default_value

    def exists(self, key: Key, value_type: Type = str) -> bool:
        return self.get(key, value_type, None) is not None

    def set(self, key: Key, value: ..., *, save: bool = True) -> bool:
        key_list = key.value.split(".")
        with self._lock:
            current_config = self._config
            for i in range(len(key_list)):
                current_key = key_list[i]
                current_value = current_config.get(current_key)
                if (i + 1) == len(key_list):
                    if current_value != value:
                        current_config[current_key] = value
                        if save:
                            return self.save()
                    return True
                if type(current_value) is not dict:
                    current_value = dict()
                    current_config[current_key] = current_value
                current_config = current_value
        return False

    def clear(self, *, save: bool = True) -> bool:
        with self._lock:
            self._config.clear()
            return self.save() if save else True

    def _updateVersion(self) -> None:
        if not self.get(self.Key.VERSION, str):
            self.set(self.Key.VERSION, Product.VERSION_STRING, save=False)


class ConfigStaticList(StaticList):
    def __init__(
        self,
        config: Config,
        config_key: Config.Key,
        source_list: Union[list, tuple],
        *,
        default_index: int,
        item_property: str,
    ) -> None:
        super().__init__(source_list, item_property=item_property)
        self._logger = Logger.classLogger(self.__class__)

        self._config = config
        self._config_key = config_key
        self._current_index = default_index
        if self._current_index >= len(self):
            self._current_index = 0

        value = self._config.get(self._config_key)
        if value:
            for i in range(len(self._list)):
                if getattr(self._list[i], self._item_property) == value:
                    self._current_index = i
                    break

    @property
    def currentIndex(self) -> int:
        return self._current_index

    def setCurrentIndex(self, index: int) -> bool:
        if index < 0 or index >= len(self._list):
            return False
        with self._config.lock:
            self._current_index = index
            return self._config.set(
                self._config_key,
                getattr(self._list[index], self._item_property),
            )

    @property
    def current(self) -> ...:
        return self._list[self._current_index]

    def setCurrent(self, value: str) -> bool:
        with self._config.lock:
            for i in range(len(self._list)):
                if getattr(self._list[i], self._item_property) == value:
                    return self.setCurrentIndex(i)
        return False


class ApplicationConfig(Config):
    class Key(Config.Key):
        VERSION: Final = "version"

        UI_LANGUAGE: Final = "ui.language"
        UI_THEME: Final = "ui.theme"
        UI_CLOSE_TO_TRAY: Final = "ui.close_to_tray"
        UI_FONT_FAMILY: Final = "ui.font.family"
        UI_FONT_SIZE: Final = "ui.font.size"

        SERVICES_FIAT_RATE: Final = "services.fiat_rate"
        SERVICES_FIAT_CURRENCY: Final = "services.fiat_currency"

        SERVICES_BLOCKCHAIN_EXPLORER: Final = "services.blockchain_explorer"

        IMPORTED_KEY_STORES: Final = "imported"

class KeyStoreConfig(Config):
    class Key(Config.Key):
        VERSION: Final = "version"

        VALUE: Final = "value"
        SEED: Final = "seed"
        SEED_PHRASE: Final = "seed_phrase"
