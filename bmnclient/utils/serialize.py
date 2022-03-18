from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Union

from .class_property import classproperty
from .string import StringUtils

DeserializedData = Optional[str, int, List, Dict]
DeserializedDict = Dict[str, DeserializedData]


class DeserializationNotSupportedError(Exception):
    def __init__(self) -> None:
        super().__init__("deserialization not supported")


def serializable(
        function: Optional[property] = None,
        **kwargs) -> Union[Callable[[property], property], property]:
    def decorator(function_: property) -> property:
        assert isinstance(function_, property)
        fget = getattr(function_, "fget")
        fget.__serializable = True
        fget.__data = kwargs
        return function_
    return decorator if function is None else decorator(function)


class Serializable:
    __serialize_map = None

    def __init__(self, *args, row_id: int = -1, **kwargs) -> None:
        self.__row_id = row_id

    def __update__(self, **kwargs) -> bool:
        row_id = kwargs.pop("row_id", None)
        if row_id is not None:
            self.rowId = row_id

        serialize_map = self.serializeMap
        for (key, value) in kwargs.items():
            key = self.__keyFromKwarg(key)
            if key not in serialize_map:
                raise KeyError(
                    "unknown property '{}' to deserialization".format(key))
            v = getattr(self.__class__, serialize_map[key]["name"])
            if v.fset:
                v.fset(self, value)
            elif v.fget(self) != value:
                raise ValueError(
                    "can't update immutable property '{}'".format(key))
        return True

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
                    cls.__serialize_map[StringUtils.toSnakeCase(name)] = dict(
                        name=name,
                        **getattr(v.fget, "__data", {}))

        return cls.__serialize_map

    def serialize(
            self,
            *,
            exclude_subclasses: bool = False,
            **options) -> DeserializedDict:
        result = {}
        for (key, data) in self.serializeMap.items():
            result[key] = self._serializeProperty(
                key,
                getattr(self, data["name"]),
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
            "can't serialize value type '{}' for key '{}'"
            .format(str(type(value)), key))

    @classmethod
    def deserialize(
            cls,
            source_data: DeserializedDict,
            *args,
            **options) -> Optional[Serializable]:
        kwargs = {
            cls.__keyToKwarg(key):
                cls._deserializeProperty(None, key, value, *args, **options)
            for key, value in source_data.items()
        }
        return cls(*args, **kwargs)

    def deserializeUpdate(
            self,
            source_data: DeserializedDict,
            **options) -> bool:
        kwargs = {
            self.__keyToKwarg(key):
                self._deserializeProperty(self, key, value, **options)
            for key, value in source_data.items()
        }
        return self.__update__(**kwargs)

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
            "can't deserialize value type '{}' for key '{}'"
            .format(str(type(value)), key))

    @classmethod
    def __keyToKwarg(cls, key: str) -> str:
        if key in ("type", ):
            return key + "_"
        return key

    @classmethod
    def __keyFromKwarg(cls, key: str) -> str:
        if key in ("type_", ):
            return key[:-1]
        return key
