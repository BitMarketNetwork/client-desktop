from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Iterator, Optional, Union


class StaticList(Sequence):
    def __init__(
            self,
            source_list: Union[list, tuple],
            *,
            item_property: str) -> None:
        self._list = source_list
        self._item_property = item_property

    def __iter__(self) -> Iterator[Any]:
        return iter(self._list)

    def __len__(self) -> int:
        return len(self._list)

    def __getitem__(self, value: Union[str, int]) -> Optional[Any]:
        if isinstance(value, str):
            for item in self._list:
                if getattr(item, self._item_property) == value:
                    return item
        elif 0 <= value <= len(self._list):
            return self._list[value]
        return None
