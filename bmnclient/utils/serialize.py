from __future__ import annotations

from collections.abc import MutableSequence
from enum import Flag, auto
from typing import (
    Callable,
    Generator,
    Generic,
    Iterable,
    Optional,
    TypeVar,
    Union)

from .class_property import classproperty
from .string import StringUtils

DeserializedData = Optional[Union[str, int, list, dict]]
DeserializedDict = dict[str, DeserializedData]


class DeserializationNotSupportedError(Exception):
    def __init__(self) -> None:
        super().__init__("deserialization not supported")


def serializable(
        function: property | None = None,
        **kwargs) -> Callable[[property], property] | property:
    def decorator(function_: property) -> property:
        assert isinstance(function_, property)
        fget = getattr(function_, "fget")
        fget.__serializable = True
        fget.__data = kwargs
        return function_
    return decorator if function is None else decorator(function)


class SerializeFlag(Flag):
    DATABASE_MODE = auto()
    PUBLIC_MODE = auto()
    PRIVATE_MODE = auto()
    EXCLUDE_SUBCLASSES = auto()


class DeserializeFlag(Flag):
    DATABASE_MODE = auto()
    NORMAL_MODE = auto()


class Serializable:
    __serialize_map = None

    def __init__(self, *args, **kwargs) -> None:
        self.__row_id = -1

    def __update__(self, **kwargs) -> bool:
        serialize_map = self.serializeMap
        for (key, value) in kwargs.items():
            key = self.kwargKeyToName(key)
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
        if self.__row_id != value:
            if self.__row_id > 0 and value != -1:
                raise RuntimeError("row id can't be changed")
            self.__row_id = value

    @classproperty
    def serializeMap(cls) -> dict[str, str]: # noqa
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

    def serialize(self, flags: SerializeFlag) -> DeserializedDict:
        return {
            key: self.serializeProperty(
                flags,
                key,
                getattr(self, data["name"]))
            for (key, data) in self.serializeMap.items()
        }

    def serializeProperty(
            self,
            flags: SerializeFlag,
            key: str,
            value: ...) -> DeserializedData:
        if isinstance(value, Serializable):
            if bool(flags & SerializeFlag.EXCLUDE_SUBCLASSES):
                return {}
            return value.serialize(flags)
        if isinstance(value, (int, str, type(None))):
            return value
        if isinstance(value, Iterable):
            return [
                self.serializeProperty(flags, key, v)
                for v in value
                if not (
                        isinstance(v, Serializable)
                        and bool(flags & SerializeFlag.EXCLUDE_SUBCLASSES)
                )
            ]

        raise TypeError(
            "can't serialize value type '{}' for key '{}'"
            .format(str(type(value)), key))

    @classmethod
    def deserialize(
            cls,
            flags: DeserializeFlag,
            source_data: DeserializedDict,
            *cls_args) -> Serializable | None:
        cls_kwargs = {
            cls.kwargKeyFromName(key):
                cls.deserializeProperty(flags, None, key, value, *cls_args)
            for key, value in source_data.items()
        }
        return cls(*cls_args, **cls_kwargs)

    def deserializeUpdate(
            self,
            flags: DeserializeFlag,
            source_data: DeserializedDict) -> bool:
        kwargs = {
            self.kwargKeyFromName(key):
                self.deserializeProperty(flags, self, key, value)
            for key, value in source_data.items()
        }
        return self.__update__(**kwargs)

    @classmethod
    def deserializeProperty(
            cls,
            flags: DeserializeFlag,
            self: Serializable | None,
            key: str,
            value: DeserializedData,
            *cls_args) -> ...:
        if isinstance(value, (int, str, type(None))):
            return value
        if isinstance(value, Iterable):
            return [
                cls.deserializeProperty(flags, self, key, v, *cls_args)
                for v in value
            ]

        raise TypeError(
            "can't deserialize value type '{}' for key '{}'"
            .format(str(type(value)), key))

    @classmethod
    def kwargKeyFromName(cls, key: str) -> str:
        if key in ("type", ):
            return key + "_"
        return key

    @classmethod
    def kwargKeyToName(cls, key: str) -> str:
        if key in ("type_", ):
            return key[:-1]
        return key


_T = TypeVar("_T", bound=Serializable)


class SerializableList(MutableSequence[Generic[_T]]):
    def __len__(self) -> int:
        raise NotImplementedError

    def __iter__(self) -> Generator[_T, None, None]:
        raise NotImplementedError

    def __getitem__(self, index: int) -> _T:
        raise NotImplementedError

    def __setitem__(self, index: int, value: ...) -> None:
        raise NotImplementedError

    def __delitem__(self, index: int) -> None:
        raise NotImplementedError

    def insert(self, index: int, value: ...) -> None:
        raise NotImplementedError

    def append(self, value: ...) -> None:
        return self.insert(-1, value)

    def clear(self) -> int:
        raise NotImplementedError


class EmptySerializableList(SerializableList):
    def __len__(self) -> int:
        return 0

    def __iter__(self) -> Iterable[_T]:
        return self

    def __next__(self) -> _T:
        raise StopIteration

    def __getitem__(self, index: int) -> _T:
        raise IndexError

    def __setitem__(self, index: int, value: ...) -> None:
        raise IndexError

    def __delitem__(self, index: int) -> None:
        raise IndexError

    def insert(self, index: int, value: ...) -> None:
        raise IndexError

    def clear(self) -> int:
        return 0
