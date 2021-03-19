# JOK++
from __future__ import annotations

from typing import Any, Dict, Optional

from .meta import classproperty
from .string import toSnakeCase


# noinspection PyPep8Naming
class serializable_property(property):
    pass


class Serializable:
    __map = None

    def __init__(self) -> None:
        self.__row_id = None

    @property
    def rowId(self) -> Optional[int]:
        return self.__row_id

    @rowId.setter
    def rowId(self, value: int) -> None:
        self.__row_id = value

    @classproperty
    def serializableMap(cls) -> Dict[str, str]: # noqa
        if cls.__map is None:
            cls.__map = {}
            for name in dir(cls):
                if isinstance(getattr(cls, name), serializable_property):
                    cls.__map[toSnakeCase(name)] = name
        return cls.__map

    def serialize(self) -> Dict[str, Any]:
        result = {}
        for (key, name) in self.serializableMap.items():
            result[key] = getattr(self, name)
        return result

    @classmethod
    def deserialize(cls, table: Dict[str, Any]) -> Serializable:
        # TODO
        raise NotImplementedError
