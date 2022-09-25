from __future__ import annotations

import json, os, re
from enum import Enum
from json.decoder import JSONDecodeError
from threading import RLock
from typing import TYPE_CHECKING
from pathlib import Path

from .logger import Logger
from .utils.static_list import StaticList
from .version import Product

if TYPE_CHECKING:
    from typing import Any, Final, Type, Union


class ConfigKey(Enum):
    VERSION: Final = "version"

    UI_LANGUAGE: Final = "ui.language"
    UI_THEME: Final = "ui.theme"
    UI_CLOSE_TO_TRAY: Final = "ui.close_to_tray"
    UI_FONT_FAMILY: Final = "ui.font.family"
    UI_FONT_SIZE: Final = "ui.font.size"

    KEY_STORE_VALUE: Final = "key_store.value"
    KEY_STORE_SEED: Final = "key_store.seed"
    KEY_STORE_SEED_PHRASE: Final = "key_store.seed_phrase"

    SERVICES_FIAT_RATE: Final = "services.fiat_rate"
    SERVICES_FIAT_CURRENCY: Final = "services.fiat_currency"

    SERVICES_BLOCKCHAIN_EXPLORER: Final = "services.blockchain_explorer"


class Config:
    def __init__(self, file_path: Path = Path()) -> None:
        self._logger = Logger.classLogger(
            self.__class__,
            (None, file_path.name if file_path else ""))
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

    def create(self, path: Path, name: str) -> None:
        configures = [x.split('.')[0] for x in os.listdir(path)
            if re.match("[^\\s]+(.*?)\\.(json|JSON)$", x)]
        if name in configures:
            new_name = name
            counter = 1
            while new_name in configures:
                new_name = f"{name} ({counter})"
                counter += 1
            name = new_name
        self._file_path = Path(f"{path}/{name}.json")
        self.save()

    def load(self) -> bool:
        with self._lock:
            try:
                with open(
                        self._file_path,
                        mode="rt",
                        encoding=Product.ENCODING,
                        errors="strict") as file:
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
                    str(error_message))
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
                        errors="strict") as file:
                    json.dump(
                        self._config,
                        file,
                        skipkeys=False,
                        indent=4,
                        sort_keys=True)
                    file.flush()
                return True
            except OSError as e:
                error_message = Logger.osErrorString(e)
            except ValueError as e:
                error_message = Logger.exceptionString(e)
            self._logger.warning(
                "Failed to write file '%s'. %s",
                self._file_path,
                str(error_message))
        return False

    def get(
            self,
            key: ConfigKey,
            value_type: Type = str,
            default_value: Any = None) -> Any:
        key_list = key.value.split('.')
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

    def exists(self, key: ConfigKey, value_type: Type = str) -> bool:
        return self.get(key, value_type, None) is not None

    def set(self, key: ConfigKey, value: Any, *, save: bool = True) -> bool:
        key_list = key.value.split('.')
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
        if not self.get(ConfigKey.VERSION, str):
            self.set(ConfigKey.VERSION, Product.VERSION_STRING, save=False)


class ConfigStaticList(StaticList):
    def __init__(
            self,
            config: Config,
            config_key: ConfigKey,
            source_list: Union[list, tuple],
            *,
            default_index: int,
            item_property: str) -> None:
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
                getattr(self._list[index], self._item_property))

    @property
    def current(self) -> Any:
        return self._list[self._current_index]

    def setCurrent(self, value: str) -> bool:
        with self._config.lock:
            for i in range(len(self._list)):
                if getattr(self._list[i], self._item_property) == value:
                    return self.setCurrentIndex(i)
        return False
