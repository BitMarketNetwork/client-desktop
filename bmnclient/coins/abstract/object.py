from __future__ import annotations

from typing import TYPE_CHECKING

from ...utils.serialize import Serializable

if TYPE_CHECKING:
    from typing import Callable, Final, Optional
    from .coin import Coin
    from ...utils.serialize import DeserializedDict


class CoinObjectModel:
    pass


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
