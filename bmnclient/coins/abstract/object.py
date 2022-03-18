from __future__ import annotations

from typing import TYPE_CHECKING

from ...logger import Logger
from ...utils.serialize import Serializable
from ...utils.string import StringUtils

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, Final, Optional, Tuple
    from .coin import Coin
    from ...database import Database
    from ...utils.serialize import DeserializedDict
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
    def database(self) -> Optional[Database]:
        return self._database

    @property
    def owner(self) -> CoinObject:
        raise NotImplementedError


class CoinObject(Serializable):
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

    def _callModel(self, callback_name: str, *args, **kwargs) -> None:
        getattr(self.model, callback_name)(*args, **kwargs)

    def _updateValue(
            self,
            action: str,
            name: str,
            new_value: Any,
            update_callback: Callable[[object, str, Any], None] = setattr
    ) -> bool:
        old_value = getattr(self, name)
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
        update_callback(self, name, new_value)
        events[1](new_value)
        return True

    @property
    def coin(self) -> Coin:
        return self._coin

    @classmethod
    def deserialize(
            cls,
            source_data: DeserializedDict,
            coin: Optional[Coin] = None,
            **options) -> Optional[CoinObject]:
        assert coin is not None
        return super().deserialize(source_data, coin, **options)


if TYPE_CHECKING:
    CoinModelFactory = Callable[[CoinObject], CoinObjectModel]
