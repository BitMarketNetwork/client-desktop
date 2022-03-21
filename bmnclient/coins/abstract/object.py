from __future__ import annotations

from typing import Callable, TYPE_CHECKING

from ...database.tables import ColumnValue
from ...logger import Logger
from ...utils import Serializable, SerializeFlag
from ...utils.string import StringUtils

if TYPE_CHECKING:
    from typing import Any, Dict, Final, Optional, Tuple, Type
    from .coin import Coin
    from ...database import Database
    from ...database.tables import AbstractTable
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
    def database(self) -> Database:
        return self._database

    @property
    def owner(self) -> CoinObject:
        raise NotImplementedError


class CoinObject(Serializable):
    _TABLE_TYPE: Optional[Type[AbstractTable]] = None

    def __init__(self, coin: Coin, row_id: int = -1) -> None:
        super().__init__(row_id=row_id)
        self._coin: Final = coin
        self.__model: Optional[CoinObject, bool] = False
        self.__value_events: Dict[str, Tuple[Callable, Callable]] = {}

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

    # TODO deprecated
    def _callModel(self, callback_name: str, *args, **kwargs) -> None:
        getattr(self.model, callback_name)(*args, **kwargs)

    def _updateValue(self, action: str, name: str, new_value: Any) -> bool:
        private_name = "_" + name
        old_value = getattr(self, private_name)
        if old_value == new_value:
            return False

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

        events[0](new_value)
        setattr(self, private_name, new_value)

        if (
                self.rowId > 0
                and self._TABLE_TYPE
                and name in self.serializeMap
        ):
            column = self.serializeMap[name].get("column", None)
            if column:
                self.model.database[self._TABLE_TYPE].update(
                    self.rowId,
                    [ColumnValue(
                        column,
                        self._serializeProperty(
                            SerializeFlag.DATABASE_MODE
                            | SerializeFlag.EXCLUDE_SUBCLASSES,
                            name,
                            new_value)
                    )])

        events[1](new_value)
        return True


# TODO deprecated, create class AbstractModelFactory
CoinModelFactory = Callable[[CoinObject], CoinObjectModel]
