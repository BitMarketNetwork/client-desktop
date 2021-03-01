# JOK++
from __future__ import annotations

from typing import Any, Iterator, TYPE_CHECKING, Union

from ..logger import Logger

if TYPE_CHECKING:
    from ..config import UserConfig


class StaticList:
    ItemType = Any

    def __init__(
            self,
            source_list: Union[list, dict, tuple],
            *,
            item_property: str) -> None:
        self._list = source_list
        self._item_property = item_property

    def __iter__(self) -> Iterator[ItemType]:
        return iter(self._list)

    def __len__(self) -> int:
        return len(self._list)

    def __getitem__(self, value: Union[str, int]) -> Any:
        if isinstance(value, str):
            for item in self._list:
                if getattr(item, self._item_property) == value:
                    return item
        elif 0 <= value <= len(self._list):
            return self._list[value]
        return None


class UserStaticList(StaticList):
    ItemType = Any

    def __init__(
            self,
            user_config: UserConfig,
            user_config_key: str,
            source_list: list,
            *,
            default_index: int,
            item_property: str) -> None:
        super().__init__(source_list, item_property=item_property)
        self._logger = Logger.getClassLogger(__name__, self.__class__)

        self._user_config = user_config
        self._user_config_key = user_config_key
        self._current_index = default_index

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
    def current(self) -> ItemType:
        return self._list[self._current_index]

    def setCurrent(self, value: str) -> bool:
        with self._user_config.lock:
            for i in range(len(self._list)):
                if getattr(self._list[i], self._item_property) == value:
                    return self.setCurrentIndex(i)
        return False
