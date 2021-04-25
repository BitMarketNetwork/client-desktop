# JOK+++
from __future__ import annotations

import json
import os
from json.decoder import JSONDecodeError
from threading import RLock
from typing import TYPE_CHECKING

from .logger import Logger
from .platform import PlatformPaths
from .version import Product

if TYPE_CHECKING:
    from typing import Any, Final, Type
    from pathlib import PurePath

# TODO move to platform
USER_CONFIG_FILE_PATH = \
    PlatformPaths.USER_APPLICATION_CONFIG_PATH / \
    "config.json"

USER_DATABASE_FILE_PATH = \
    PlatformPaths.USER_APPLICATION_CONFIG_PATH / \
    "database.db"


class UserConfig:
    KEY_VERSION: Final = "version"

    KEY_UI_LANGUAGE: Final = "ui.language"
    KEY_UI_THEME: Final = "ui.theme"
    KEY_UI_HIDE_TO_TRAY: Final = "ui.hide_to_tray"
    KEY_UI_FONT_FAMILY: Final = "ui.font.family"
    KEY_UI_FONT_SIZE: Final = "ui.font.size"

    KEY_KEY_STORE_VALUE: Final = "key_store.value"
    KEY_KEY_STORE_SEED: Final = "key_store.seed"
    KEY_KEY_STORE_SEED_PHRASE: Final = "key_store.seed_phrase"

    KEY_SERVICES_FIAT_RATE: Final = "services.fiat_rate"
    KEY_SERVICES_FIAT_CURRENCY: Final = "services.fiat_currency"

    def __init__(
            self,
            file_path: PurePath = USER_CONFIG_FILE_PATH) -> None:
        self._logger = Logger.getClassLogger(__name__, self.__class__)
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
                error_message = Logger.osErrorToString(e)
            except JSONDecodeError as e:
                error_message = Logger.jsonDecodeErrorToString(e)
            except ValueError as e:
                error_message = Logger.exceptionToString(e)

            self._logger.warning(
                "Failed to read file \"%s\". %s",
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
                error_message = Logger.osErrorToString(e)
            except ValueError as e:
                error_message = Logger.exceptionToString(e)
            self._logger.warning(
                "Failed to write file \"%s\". %s",
                self._file_path,
                str(error_message))
        return False

    def get(
            self,
            key: str,
            value_type: Type = str,
            default_value: Any = None) -> Any:
        key_list = key.split('.')
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

    def exists(self, key: str, value_type: Type = str) -> bool:
        return self.get(key, value_type, None) is not None

    def set(self, key: str, value: Any, *, save: bool = True) -> bool:
        key_list = key.split('.')
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
        if not self.get(self.KEY_VERSION, str):
            self.set(self.KEY_VERSION, Product.VERSION_STRING, save=False)
