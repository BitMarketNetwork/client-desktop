from __future__ import annotations

from typing import TYPE_CHECKING

from ...utils.serialize import Serializable

if TYPE_CHECKING:
    from typing import Optional
    from .coin import Coin
    from ...utils.serialize import DeserializedDict


class _CoinSerializable(Serializable):
    @classmethod
    def deserialize(
            cls,
            source_data: DeserializedDict,
            coin: Optional[Coin] = None,
            **options) -> Optional[_CoinSerializable]:
        assert coin is not None
        return super().deserialize(source_data, coin, **options)
