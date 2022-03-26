from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, TYPE_CHECKING

from ...database.tables import ColumnValue
from ...logger import Logger
from ...utils import Serializable, SerializeFlag
from ...utils.string import StringUtils

if TYPE_CHECKING:
    import logging
    from typing import Any, Dict, Final, Generator, Optional, Tuple
    from .coin import Coin
    from ...database import Database
    from ...database.tables import AbstractSerializableTable
    from ...utils.string import ClassStringKeyTuple


class CoinObjectModel:
    def __init__(
            self,
            *args,
            database: Database,
            name_key_tuple: Tuple[ClassStringKeyTuple, ...],
            **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._logger = Logger.classLogger(self.__class__, *name_key_tuple)
        self._database = database

    @property
    def logger(self) -> logging.Logger:
        return self._logger

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
            super().__init_subclass__(*args, **kwargs)
            cls.__TABLE_TYPE = table_type
        else:
            super().__init_subclass__(*args, **kwargs)

    def __init__(
            self,
            coin: Coin,
            kwargs,
            *,
            enable_table: bool = True) -> None:
        super().__init__(row_id=-1)
        self._coin: Final = coin
        self.__model: Optional[CoinObject, bool] = False
        self.__value_events: Dict[str, Tuple[Callable, Callable]] = {}
        self.__enable_table = enable_table

        if self is not self._coin and self._isTableAvailable:
            if self._table.completeSerializable(self, kwargs) > 0:
                assert self.rowId > 0

    def __eq__(self, other: CoinObject) -> bool:
        return (
                isinstance(other, self.__class__)
                and self._coin == other._coin
        )

    def __hash__(self) -> int:
        return hash((self._coin, ))

    @property
    def model(self) -> CoinObjectModel:
        if self.__model is False:
            self.__model = self._coin.modelFactory(self)
        return self.__model

    @property
    def coin(self) -> Coin:
        return self._coin

    @property
    def _isTableAvailable(self) -> bool:
        return (
                self.__TABLE_TYPE
                and self.__enable_table
                and self._coin.model.database.isOpen
        )

    @property
    def _table(self) -> AbstractSerializableTable:
        return self._coin.model.database[self.__TABLE_TYPE]

    def save(self) -> bool:
        if self._isTableAvailable and self._table.saveSerializable(self) > 0:
            assert self.rowId > 0
            return True
        return False

    def load(self) -> bool:
        if self._isTableAvailable and self._table.loadSerializable(self):
            assert self.rowId > 0
            return True
        return False

    def remove(self) -> bool:
        if self._isTableAvailable and self._table.removeSerializable(self):
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
            new_value: Any) -> bool:
        private_name = "_" + name

        old_value = getattr(self, private_name)
        if old_value == new_value:
            return False

        with self._modelEvent(action, name, new_value):
            setattr(self, private_name, new_value)
            if (
                    self.rowId > 0
                    and self.__TABLE_TYPE
                    and name in self.serializeMap
            ):
                column = self.__TABLE_TYPE.ColumnEnum.get(name)
                if column:
                    self.model.database[self.__TABLE_TYPE].update(
                        self.rowId,
                        [ColumnValue(
                            column,
                            self.serializeProperty(
                                SerializeFlag.DATABASE_MODE
                                | SerializeFlag.EXCLUDE_SUBCLASSES,
                                name,
                                new_value)
                        )])
        return True


# TODO deprecated, create class AbstractModelFactory
CoinModelFactory = Callable[[CoinObject], CoinObjectModel]
