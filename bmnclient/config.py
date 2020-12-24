# JOK+
import json
import os
from threading import RLock
from pathlib import PurePath
from typing import Any

from bmnclient import platform, version
from bmnclient.logger import getClassLogger, osErrorToString

USER_CONFIG_FILE_PATH = \
    platform.USER_APPLICATION_CONFIG_PATH / \
    "config.json"

USER_DATABASE_FILE_PATH = \
    platform.USER_APPLICATION_CONFIG_PATH / \
    "database.db"

KEY_VERSION = "version"
KEY_SERVER_VERSION = "server_version"  # TODO kill

KEY_UI_LANGUAGE = "ui.language"
KEY_UI_THEME = "ui.theme"
KEY_UI_HIDE_TO_TRAY = "ui.hide_to_tray"

KEY_WALLET_HASH = "wallet.hash"
KEY_WALLET_SALT = "wallet.salt"
KEY_WALLET_SEED = "wallet.seed"


class UserConfig:
    def __init__(self, file_path=USER_CONFIG_FILE_PATH) -> None:
        assert isinstance(file_path, PurePath)
        self._logger = getClassLogger(__name__, self.__class__)
        self._file_path = file_path
        self._config = dict()
        self._lock = RLock()  # TODO ReadWriteLock

    def load(self) -> bool:
        with self._lock:
            try:
                with open(
                        self._file_path,
                        mode='rt',
                        encoding=version.PYTHON_ENCODING,
                        errors='replace') as file:
                    self._config = json.load(file)
                return True
            except OSError as e:
                self._logger.warning(
                    "Failed to open configuration file \"%s\". %s",
                    self._file_path,
                    osErrorToString(e))
            except json.decoder.JSONDecodeError as e:
                self._logger.warning(
                    "Failed to parse configuration file \"%s\". "
                    "Offset %i:%i: %s",
                    self._file_path,
                    e.lineno,
                    e.pos,
                    e.msg)
            self._config = dict()
        return False

    def save(self) -> bool:
        with self._lock:
            try:
                os.makedirs(self._file_path.parent, exist_ok=True)
                with open(
                        self._file_path,
                        mode='w+t',
                        encoding=version.PYTHON_ENCODING,
                        errors='replace') as file:
                    json.dump(
                        self._config,
                        file,
                        skipkeys=False,
                        indent=4,
                        sort_keys=True)
                    file.flush()
                return True
            except OSError as e:
                self._logger.warning(
                    "Failed to write configuration file \"%s\". %s",
                    self._file_path,
                    osErrorToString(e))
        return False

    def get(self, key, value_type=str, default_value=None) -> Any:
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

    def exists(self, key, value_type=str) -> bool:
        return self.get(key, value_type, None) is not None

    def set(self, key, value, save=True) -> bool:
        key_list = key.split('.')
        with self._lock:
            current_config = self._config
            for i in range(len(key_list)):
                current_key = key_list[i]
                current_value = current_config.get(current_key)
                if (i + 1) == len(key_list):
                    if current_value == value:
                        return False
                    current_config[current_key] = value
                    if save:
                        return self.save()
                    return True
                if type(current_value) is not dict:
                    current_value = dict()
                    current_config[current_key] = current_value
                current_config = current_value
        return False
