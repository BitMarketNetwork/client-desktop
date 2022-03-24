from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, TYPE_CHECKING

from ...database.tables import ColumnValue
from ...logger import Logger
from ...utils import Serializable, SerializeFlag
from ...utils.string import StringUtils

if TYPE_CHECKING:
    import logging
    from typing import (
        Any,
        Dict,
        Final,
        Generator,
        Optional,
        Sequence,
        Tuple,
        Type)
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
    _TABLE_TYPE: Optional[Type[AbstractSerializableTable]] = None

    def __init__(
            self,
            coin: Coin,
            row_id: int,
            kwargs,
            *,
            complete_key_columns: Sequence[ColumnValue] = tuple()) -> None:
        super().__init__(row_id=row_id)
        self._coin: Final = coin
        self.__model: Optional[CoinObject, bool] = False
        self.__value_events: Dict[str, Tuple[Callable, Callable]] = {}

        if (
                complete_key_columns
                and self is not self._coin  # model not ready
                and self._TABLE_TYPE
                and self._coin.model.database.isOpen
        ):
            table = self._coin.model.database[self._TABLE_TYPE]
            count = table.completeSerializable(
                self,
                row_id,
                complete_key_columns,
                kwargs)
            self._coin.model.logger.debug(
                "%d columns completed from database for %s: %s",
                count,
                self.__class__.__name__,
                ", ".join(
                    f"{c.column} = '{str(c.value)}'"
                    for c in complete_key_columns)
            )

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

    def save(self) -> bool:
        raise NotImplementedError

    def load(self) -> bool:
        raise NotImplementedError

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
                    and self._TABLE_TYPE
                    and name in self.serializeMap
            ):
                column = self._TABLE_TYPE.ColumnEnum.get(name)
                if column:
                    self.model.database[self._TABLE_TYPE].update(
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
