from __future__ import annotations

from contextlib import contextmanager
from enum import IntEnum
from typing import (
    Callable,
    Final,
    Generator,
    Iterable,
    TYPE_CHECKING,
    TypeVar)

from ...database.tables import ColumnValue, SerializableTable
from ...logger import Logger
from ...utils import (
    EmptySerializableList,
    Serializable,
    SerializableList,
    SerializeFlag)
from ...utils.string import StringUtils

if TYPE_CHECKING:
    import logging
    from .coin import Coin
    from ...database import Database
    from ...utils.string import ClassStringKeyTuple


class CoinObjectModel:
    def __init__(
            self,
            *args,
            name_key_tuple: tuple[ClassStringKeyTuple, ...],
            **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._logger = Logger.classLogger(self.__class__, *name_key_tuple)

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def owner(self) -> CoinObject:
        raise NotImplementedError


class CoinRootObjectModel(CoinObjectModel):
    def __init__(self, *args, database: Database, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._database = database

    @property
    def database(self) -> Database:
        return self._database

    @property
    def owner(self) -> CoinObject:
        raise NotImplementedError


class CoinObject(Serializable):
    def __init_subclass__(cls, *args, **kwargs) -> None:
        if (
                not hasattr(cls, "_CoinObject__TABLE_TYPE")
                or "table_type" in kwargs
        ):
            table_type = kwargs.pop("table_type")
            associated_table_type = kwargs.pop("associated_table_type", None)
            super().__init_subclass__(*args, **kwargs)
            cls.__TABLE_TYPE = table_type
            cls.__ASSOCIATED_TABLE_TYPE = associated_table_type
        else:
            super().__init_subclass__(*args, **kwargs)

    def __init__(
            self,
            coin: Coin,
            kwargs,
            *,
            enable_table: bool = True) -> None:
        super().__init__()
        self._coin: Final = coin
        self.__model: CoinObjectModel | bool | None = False
        self.__value_events: dict[str, tuple[Callable, Callable]] = {}
        self.__enable_table = enable_table
        self.__deferred_save_list: list[list[CoinObject]] = []

        if self is not self._coin and (t := self._openTable(force=True)):
            if t.completeSerializable(self, kwargs) > 0:
                assert self.rowId > 0

    def __eq__(self, other: CoinObject) -> bool:
        if not isinstance(other, self.__class__):
            return False
        if self is not self._coin:
            if self._coin != other._coin:
                return False
        return True

    def __hash__(self) -> int:
        if self is not self._coin:
            return hash((self._coin, ))
        return 0

    @property
    def model(self) -> CoinObjectModel | CoinRootObjectModel:
        if self.__model is False:
            self.__model = self._coin.modelFactory(self)
        return self.__model

    @property
    def coin(self) -> Coin:
        return self._coin

    def associate(self, object_: CoinObject) -> bool | None:
        if not self.__ASSOCIATED_TABLE_TYPE:
            return None
        if not (t := self._openTable(self.__ASSOCIATED_TABLE_TYPE)):
            return False
        return t.associate(self, object_)

    def _appendDeferredSave(
            self,
            object_list: Iterable[Callable[[CoinObject], CoinObject]]) -> None:
        if object_list:
            self.__deferred_save_list.append([o(self) for o in object_list])

    def save(self) -> bool:
        if not (t := self._openTable(force=True)):
            return False
        with self._coin.model.database.transaction(allow_in_transaction=True):
            if t.saveSerializable(self) <= 0:
                return False
            assert self.rowId > 0

            for object_list in self.__deferred_save_list:
                for object_ in object_list:
                    if not object_.save():
                        return False
                    if self.associate(object_) is False:
                        return False
            self.__deferred_save_list.clear()
        return True

    def load(self) -> bool:
        if (t := self._openTable(force=True)) and t.loadSerializable(self):
            assert self.rowId > 0
            return True
        return False

    def remove(self) -> bool:
        if (t := self._openTable(force=True)) and t.removeSerializable(self):
            assert self.rowId == -1
            return True
        return False

    # TODO deprecated
    def _callModel(self, callback_name: str, *args, **kwargs) -> None:
        getattr(self.model, callback_name)(*args, **kwargs)

    @contextmanager
    def _modelEvent(
            self,
            action: str,
            name: str,
            *args) -> Generator[None, None, None]:
        events_name = name + "[" + action + "]"
        events = self.__value_events.get(events_name, None)
        if not events:
            assert action in ("update", "set", "append")
            action = action.capitalize()
            suffix = StringUtils.toCamelCase(name.strip("_"), first_lower=False)
            events = (
                getattr(self.model, "before" + action + suffix),
                getattr(self.model, "after" + action + suffix))
            self.__value_events[events_name] = events
        events[0](*args)
        yield None
        events[1](*args)

    def _updateValue(
            self,
            action: str,
            name: str,
            new_value: ...,
            *,
            on_update: Callable[[], None] | None = None) -> bool:
        private_name = "_" + name

        old_value = getattr(self, private_name)
        if old_value == new_value:
            return False

        with self._modelEvent(action, name, new_value):
            setattr(self, private_name, new_value)
            if (
                    (table := self._openTable())
                    and name in self.serializeMap
                    and (column := self.__TABLE_TYPE.ColumnEnum.get(name))
            ):
                columns = [ColumnValue(
                    column,
                    self.serializeProperty(
                        SerializeFlag.DATABASE_MODE
                        | SerializeFlag.EXCLUDE_SUBCLASSES,
                        name,
                        new_value)
                )]
                if on_update:
                    with table.database.transaction(allow_in_transaction=True):
                        table.update(self.rowId, columns)
                        on_update()
                else:
                    table.update(self.rowId, columns)
            else:
                if on_update:
                    on_update()
        return True

    _TableT = TypeVar("_TableT", bound=SerializableTable)

    def _openTable(
            self,
            table_type: type(_TableT) | None = None,
            *,
            force: bool = False) -> _TableT | None:
        if not force and self.rowId <= 0:
            return None
        if table_type is None:
            table_type = self.__TABLE_TYPE
        if not table_type or not self.__enable_table:
            return None
        if not self._coin.model.database.isOpen:
            return None
        return self._coin.model.database[table_type]

    def _rowList(
            self,
            table_type: type(SerializableTable),
            *args,
            **kwargs
    ) -> SerializableList:
        if t := self._openTable(table_type):
            if result := t.rowList(self, *args, **kwargs):
                return result
        return EmptySerializableList()


# TODO deprecated, create class AbstractModelFactory
CoinModelFactory = Callable[[CoinObject], CoinObjectModel]
