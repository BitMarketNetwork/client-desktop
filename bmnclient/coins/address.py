# JOK++
from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from ..utils.serialize import Serializable, serializable_property

if TYPE_CHECKING:
    from .coin import AbstractCoin
    from .tx import AbstractTx


class AddressModelInterface:
    def afterSetAmount(self) -> None:
        raise NotImplementedError

    def afterSetLabel(self) -> None:
        raise NotImplementedError

    def afterSetComment(self) -> None:
        raise NotImplementedError

    def beforeAppendTx(self, tx: AbstractTx) -> None:
        raise NotImplementedError

    def afterAppendTx(self, tx: AbstractTx) -> None:
        raise NotImplementedError


class AbstractAddress(Serializable):
    def __init__(
            self,
            coin: AbstractCoin,
            *,
            name: str,
            amount: int = 0,
            label: str = "",
            comment: str = "") -> None:
        super().__init__()

        self._coin = coin
        self._name = name
        self._data = b""  # TODO
        self._amount = amount
        self._label = label
        self._comment = comment
        self._tx_list = []  # TODO enable enable deserialize

        self._model: Optional[AddressModelInterface] = \
            self._coin.model_factory(self)

    @property
    def model(self) -> Optional[AddressModelInterface]:
        return self._model

    @property
    def coin(self) -> AbstractCoin:
        return self._coin

    @serializable_property
    def name(self) -> str:
        return self._name

    @classmethod
    def decode(
            cls,
            source: str,
            *,
            coin: AbstractCoin) -> Optional[AbstractAddress]:
        return None

    @property
    def data(self) -> bytes:
        return self._data

    @serializable_property
    def amount(self) -> int:
        return self._amount

    @amount.setter
    def amount(self, value: int) -> None:
        if self._amount != value:
            self._amount = value
            if self._model:
                self._model.afterSetAmount()

    @serializable_property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, value: str) -> None:
        if self._label != value:
            self._label = value
            if self._model:
                self._model.afterSetLabel()

    @serializable_property
    def comment(self) -> str:
        return self._comment

    @comment.setter
    def comment(self, value: str) -> None:
        if self._comment != value:
            self._comment = value
            if self._model:
                self._model.afterSetComment()

    @property
    def txList(self) -> List[AbstractTx]:
        return self._tx_list

    def findTxByName(self, name: str) -> Optional[AbstractTx]:
        name = name.strip().casefold()  # TODO tmp, old wrapper
        for tx in self._tx_list:
            if name == tx.name.casefold():
                return tx
        return None

    def appendTx(self, tx: AbstractTx) -> bool:
        # TODO tmp, old wrapper
        if self.findTxByName(tx.name) is not None:  # noqa
            return False

        if self._model:
            self._model.beforeAppendTx(tx)
        self._tx_list.append(tx)
        if self._model:
            self._model.afterAppendTx(tx)

        return True
