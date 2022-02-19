from __future__ import annotations

from typing import TYPE_CHECKING

from .class_property import classproperty
from .string import StringUtils

if TYPE_CHECKING:
    from typing import Any, Dict, List, Optional
    DeserializedData = Optional[str, int, List, Dict]
    DeserializedDict = Dict[str, DeserializedData]


class DeserializationNotSupportedError(Exception):
    def __init__(self) -> None:
        super().__init__("deserialization not supported")


def serializable(func: property) -> property:
    assert isinstance(func, property)
    getattr(func, "fget").__serializable = True
    return func


class Serializable:
    __serialize_map = None

    def __init__(self, *args, row_id: int = -1, **kwargs) -> None:
        self.__row_id = row_id

    @property
    def rowId(self) -> int:
        return self.__row_id

    @rowId.setter
    def rowId(self, value: int) -> None:
        self.__row_id = value

    @classproperty
    def serializeMap(cls) -> Dict[str, str]: # noqa
        if cls.__serialize_map is None:
            cls.__serialize_map = {}
            for name in dir(cls):
                v = getattr(cls, name)
                if (
                        isinstance(v, property)
                        and getattr(v.fget, "__serializable", None)
                ):
                    cls.__serialize_map[StringUtils.toSnakeCase(name)] = name
        return cls.__serialize_map

    def serialize(
            self,
            *,
            exclude_subclasses: bool = False,
            **options) -> DeserializedDict:
        result = {}
        for (key, name) in self.serializeMap.items():
            result[key] = self._serializeProperty(
                key,
                getattr(self, name),
                exclude_subclasses=exclude_subclasses,
                **options)
        return result

    def _serializeProperty(
            self,
            key: str,
            value: Any,
            *,
            exclude_subclasses: bool = False,
            **options) -> DeserializedData:
        if isinstance(value, Serializable):
            if exclude_subclasses:
                return {}
            return value.serialize(**options)
        if isinstance(value, (int, str, type(None))):
            return value
        if isinstance(value, list):
            return [self._serializeProperty(key, v, **options) for v in value]

        raise TypeError(
            "can't serialize value of type '{}'"
            .format(str(type(value))))

    @classmethod
    def deserialize(
            cls,
            source_data: DeserializedDict,
            *args,
            **options) -> Optional[Serializable]:
        kwargs = {
            key: cls._deserializeProperty(None, key, value, *args, **options)
            for key, value in source_data.items()
        }
        return cls._deserialize(*args, **kwargs)

    @classmethod
    def _deserializeProperty(
            cls,
            self: Optional[Serializable],
            key: str,
            value: DeserializedData,
            *args,
            **options) -> Any:
        if isinstance(value, (int, str, type(None))):
            return value
        if isinstance(value, list):
            return [
                cls._deserializeProperty(self, key, v, *args, **options)
                for v in value
            ]

        raise TypeError(
            "can't deserialize value of type '{}'"
            .format(str(type(value))))

    @classmethod
    def _deserialize(cls, *args, **kwargs) -> Optional[Serializable]:
        return cls(*args, **kwargs)
