# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from .meta import classproperty
from .string import StringUtils

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, List, Optional, Tuple
    DeserializedData = Dict[str, Optional[str, int, List, Dict]]


class DeserializationNotSupportedError(Exception):
    def __init__(self) -> None:
        super().__init__("deserialization not supported")


def serializable(func) -> Any:
    assert isinstance(func, property)
    getattr(func, "fget").__serializable = True
    return func


class Serializable:
    __map = None

    def __init__(self, *args, **kwargs) -> None:
        self.__row_id: Optional[int] = None

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
                    cls.__map[StringUtils.toSnakeCase(name)] = name
        return cls.__map

    def serialize(self) -> DeserializedData:
        result = {}
        for (key, name) in self.serializableMap.items():
            result[key] = self._serializeProperty(key, getattr(self, name))
        return result

    def _serializeProperty(self, key: str, value: Any) -> Any:
        if isinstance(value, Serializable):
            return value.serialize()
        if isinstance(value, (int, str, type(None))):
            return value
        if isinstance(value, list):
            return [self._serializeProperty(key, v) for v in value]

        raise TypeError(
            "cannot serialize value of type '{}'"
            .format(str(type(value))))

    @classmethod
    def deserialize(
            cls,
            *args,
            deserialize_create: Callable[[...], Serializable] = None,
            **kwargs) -> Optional[Serializable]:
        kwargs = {
            k: cls._deserializeProperty(args, k, v) for k, v in kwargs.items()
        }
        if deserialize_create is not None:
            return deserialize_create(*args, **kwargs)
        else:
            return cls(*args, **kwargs)

    @classmethod
    def _deserializeProperty(
            cls,
            args: Tuple[Any],
            key: str,
            value: Any) -> Any:
        if isinstance(value, (int, str, type(None))):
            return value
        if isinstance(value, list):
            return [cls._deserializeProperty(args, key, v) for v in value]

        raise TypeError(
            "cannot deserialize value of type '{}'"
            .format(str(type(value))))
