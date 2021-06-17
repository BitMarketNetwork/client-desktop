# JOK4
from __future__ import annotations

import json
import os
from enum import Enum
from json.decoder import JSONDecodeError
from threading import RLock
from typing import TYPE_CHECKING

from .logger import Logger
from .utils.static_list import StaticList
from .version import Product

if TYPE_CHECKING:
    from typing import Any, Final, Type, Union
    from pathlib import PurePath


class UserConfig:
    class Key(Enum):
        VERSION: Final = "version"

        UI_LANGUAGE: Final = "ui.language"
        UI_THEME: Final = "ui.theme"
        UI_HIDE_TO_TRAY: Final = "ui.hide_to_tray"
        UI_FONT_FAMILY: Final = "ui.font.family"
        UI_FONT_SIZE: Final = "ui.font.size"

        KEY_STORE_VALUE: Final = "key_store.value"
        KEY_STORE_SEED: Final = "key_store.seed"
        KEY_STORE_SEED_PHRASE: Final = "key_store.seed_phrase"

        SERVICES_FIAT_RATE: Final = "services.fiat_rate"
        SERVICES_FIAT_CURRENCY: Final = "services.fiat_currency"

    def __init__(self, file_path: PurePath) -> None:
        self._logger = Logger.classLogger(
            self.__class__,
            (None, file_path.name))
        self._file_path = file_path
        self._config = dict()
        self._lock = RLock()

    @property
    def lock(self) -> RLock:
        return self._lock

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
            except OSError as e:
                error_message = Logger.osErrorString(e)
            except JSONDecodeError as e:
                error_message = Logger.jsonDecodeErrorString(e)
            except ValueError as e:
                error_message = Logger.exceptionString(e)

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
                os.makedirs(self._file_path.parent, exist_ok=True)
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
            key: Key,
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

    def exists(self, key: Key, value_type: Type = str) -> bool:
        return self.get(key, value_type, None) is not None

    def set(self, key: Key, value: Any, *, save: bool = True) -> bool:
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

    def _updateVersion(self) -> None:
        if not self.get(self.Key.VERSION, str):
            self.set(self.Key.VERSION, Product.VERSION_STRING, save=False)


class UserConfigStaticList(StaticList):
    def __init__(
            self,
            user_config: UserConfig,
            user_config_key: UserConfig.Key,
            source_list: Union[list, tuple],
            *,
            default_index: int,
            item_property: str) -> None:
        super().__init__(source_list, item_property=item_property)
        self._logger = Logger.classLogger(self.__class__)

        self._user_config = user_config
        self._user_config_key = user_config_key
        self._current_index = default_index
        if self._current_index >= len(self):
            self._current_index = 0

        value = self._user_config.get(self._user_config_key)
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
        with self._user_config.lock:
            self._current_index = index
            return self._user_config.set(
                self._user_config_key,
                getattr(self._list[index], self._item_property))

    @property
    def current(self) -> Any:
        return self._list[self._current_index]

    def setCurrent(self, value: str) -> bool:
        with self._user_config.lock:
            for i in range(len(self._list)):
                if getattr(self._list[i], self._item_property) == value:
                    return self.setCurrentIndex(i)
        return False
