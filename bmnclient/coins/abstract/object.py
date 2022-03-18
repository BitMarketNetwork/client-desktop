from __future__ import annotations

from typing import TYPE_CHECKING

from ...logger import Logger
from ...utils.serialize import Serializable

if TYPE_CHECKING:
    from typing import Callable, Final, Optional, Tuple
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


class CoinObject(Serializable):
    def __init__(self, coin: Coin, row_id: int = -1) -> None:
        super().__init__(row_id=row_id)
        self._coin: Final = coin
        self.__model: Optional[CoinObject, bool] = False

    def __eq__(self, other: CoinObject) -> bool:
        return (
                isinstance(other, self.__class__)
                and self._coin == other._coin
        )

    def __hash__(self) -> int:
        return hash((self._coin, ))

    @property
    def model(self) -> Optional[CoinObjectModel]:
        if self.__model is False:
            self.__model = self._coin.modelFactory(self)
        return self.__model

    def _callModel(self, callback_name: str, *args, **kwargs) -> bool:
        model = self.model
        if model:
            getattr(model, callback_name)(*args, **kwargs)
            return True
        return False

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
