from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, Type, Union

from .meta import classproperty
from .string import toSnakeCase


class ParseError(LookupError):
    pass


def parseItemKey(
        item: Union[dict, list],
        key_name: Union[str, int],
        value_type: Type,
        default_value: Any = None) -> Any:
    try:
        value = value_type(item[key_name])
    except (KeyError, IndexError):
        if default_value is None:
            raise ParseError(
                "key \"{}\" not found".format(str(key_name)))
        value = default_value
    except (TypeError, ValueError):
        raise ParseError(
            "invalid value for key \"{}\"".format(str(key_name)))
    return value


def serializable(func) -> Any:
    assert isinstance(func, property)
    getattr(func, "fget").__serializable = True
    return func


class Serializable:
    __map = None

    def __init__(self, *args, **kwargs) -> None:
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
                v = getattr(cls, name)
                if (
                        isinstance(v, property) and
                        hasattr(v.fget, "__serializable") and
                        getattr(v.fget, "__serializable")
                ):
                    cls.__map[toSnakeCase(name)] = name
        return cls.__map

    def serialize(self) -> Dict[str, Any]:
        result = {}
        for (key, name) in self.serializableMap.items():
            result[key] = self._serialize(getattr(self, name))
        return result

    def _serialize(self, value: Any) -> Any:
        if isinstance(value, Serializable):
            return value.serialize()
        if isinstance(value, (int, str)):
            return value
        if isinstance(value, list):
            return [self._serialize(v) for v in value]

        raise TypeError(
            "cannot serialize value of type \"{}\"."
            .format(str(type(value))))

    @classmethod
    def deserialize(cls, *args, **kwargs) -> Serializable:
        kwargs = {k: cls._deserialize(args, k, v) for k, v in kwargs.items()}
        return cls(*args, **kwargs)

    @classmethod
    def _deserialize(cls, args: Tuple[Any], key: str, value: Any) -> Any:
        if isinstance(value, (int, str)):
            return value
        if isinstance(value, list):
            return [cls._deserialize(args, key, v) for v in value]

        raise TypeError(
            "cannot deserialize value of type \"{}\"."
            .format(str(type(value))))
