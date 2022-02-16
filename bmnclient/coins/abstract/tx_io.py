from __future__ import annotations

from typing import TYPE_CHECKING

from ...utils.serialize import Serializable, serializable

if TYPE_CHECKING:
    from typing import Optional
    from .coin import Coin
    from ...utils.serialize import DeserializedDict


class _Io(Serializable):
    def __init__(
            self,
            coin: Coin,
            *,
            row_id: int = -1,
            index: int,
            output_type: str,
            address_name: Optional[str],
            amount: int) -> None:
        super().__init__(row_id=row_id)
        self._coin = coin
        self._index = index
        self._output_type = output_type

        if not address_name:
            self._address = self._coin.Address.createNullData(
                self._coin,
                amount=amount)
        else:
            self._address = self._coin.Address.decode(
                self._coin,
                name=address_name,
                amount=amount)
            if self._address is None:
                self._address = self._coin.Address.createNullData(
                    self._coin,
                    name=address_name or "UNKNOWN",
                    amount=amount)

    def __eq__(self, other: Coin.Tx.Io) -> bool:
        return (
                isinstance(other, self.__class__)
                and self._coin == other._coin
                and self._index == other.index
                and self._output_type == other._output_type
                and self._address == other.address
                and self._address.amount == other._address.amount
        )

    def __hash__(self) -> int:
        return hash((
            self._coin,
            self._index,
            self._output_type,
            self._address,
            self._address.amount
        ))

    @classmethod
    def deserialize(
            cls,
            source_data: DeserializedDict,
            coin: Optional[Coin] = None,
            **options) -> Optional[Coin.Tx.Io]:
        assert coin is not None
        return super().deserialize(source_data, coin, **options)

    @serializable
    @property
    def index(self) -> index:
        return self._index

    @serializable
    @property
    def outputType(self) -> str:
        return self._output_type

    @serializable
    @property
    def addressName(self) -> Optional[str]:
        return self._address.name if not self._address.isNullData else None

    @property
    def address(self) -> Coin.Address:
        return self._address

    @serializable
    @property
    def amount(self) -> int:
        return self._address.amount
