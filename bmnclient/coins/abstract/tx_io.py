from __future__ import annotations

from typing import TYPE_CHECKING

from .object import CoinObject, CoinObjectModel
from ...utils.serialize import serializable

if TYPE_CHECKING:
    from typing import Final, Optional
    from .coin import Coin


class _Model(CoinObjectModel):
    def __init__(self, *args, io: Coin.Tx.Io, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._io = io

    @property
    def owner(self) -> Coin.Tx.Io:
        return self._io


class _Io(CoinObject):
    Model = _Model

    def __init__(
            self,
            coin: Coin,
            address: Optional[Coin.Address] = None,
            *,
            row_id: int = -1,
            index: int,
            output_type: str,
            address_name: Optional[str],
            amount: int) -> None:
        super().__init__(coin, row_id=row_id)
        if address is not None:
            assert not address_name
            assert coin is address.coin
        elif not address_name:
            address = coin.Address.createNullData(coin)
        else:
            address = coin.Address.createFromName(coin, name=address_name)
            if address is None:
                address = coin.Address.createNullData(
                    coin,
                    name="~" + address_name.strip()[:10] + "~")

        self._index: Final = index
        self._output_type: Final = output_type
        self._address: Final = address
        self._amount: Final = amount

    def __eq__(self, other: _Io) -> bool:
        return (
                super().__eq__(other)
                and self._index == other.index
                and self._output_type == other._output_type
                and self._address == other.address
                and self._amount == other._amount
        )

    def __hash__(self) -> int:
        return hash((
            super().__hash__(),
            self._index,
            self._output_type,
            self._address,
            self._amount
        ))

    @serializable
    @property
    def index(self) -> int:
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
        return self._amount
