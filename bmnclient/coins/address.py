# JOK+++
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from ..utils.serialize import Serializable, serializable

if TYPE_CHECKING:
    from typing import List, Optional
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
    class Type(Enum):
        # Tuple(version, excepted_size, friendly_name)
        pass

    def __init__(
            self,
            coin: AbstractCoin,
            *,
            name: str,
            type_: Optional[Type],
            data: bytes = b"",
            amount: int = 0,
            label: str = "",
            comment: str = "") -> None:
        super().__init__()

        self._coin = coin
        self._name = name.strip()
        self._type = type_
        self._data = data
        self._amount = amount
        self._label = label
        self._comment = comment
        self._tx_list = []  # TODO enable deserialize

        self._model: Optional[AddressModelInterface] = \
            self._coin.model_factory(self)

    @property
    def model(self) -> Optional[AddressModelInterface]:
        return self._model

    @property
    def coin(self) -> AbstractCoin:
        return self._coin

    @serializable
    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> Optional[Type]:
        return self._type

    @classmethod
    def decode(
            cls,
            coin: AbstractCoin,
            **kwargs) -> Optional[AbstractAddress]:
        return None

    @property
    def data(self) -> bytes:
        return self._data

    @serializable
    @property
    def amount(self) -> int:
        return self._amount

    @amount.setter
    def amount(self, value: int) -> None:
        if self._amount != value:
            self._amount = value
            if self._model:
                self._model.afterSetAmount()

    @serializable
    @property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, value: str) -> None:
        if self._label != value:
            self._label = value
            if self._model:
                self._model.afterSetLabel()

    @serializable
    @property
    def comment(self) -> str:
        return self._comment

    @comment.setter
    def comment(self, value: str) -> None:
        if self._comment != value:
            self._comment = value
            if self._model:
                self._model.afterSetComment()

    @property
    def readOnly(self) -> bool:
        return True  # TODO

    @property
    def txList(self) -> List[AbstractTx]:
        return self._tx_list

    def appendTx(self, tx: AbstractTx) -> bool:
        for etx in self._tx_list:
            if tx.name != etx.name:
                continue
            if etx.height == -1:
                etx.height = tx.height
                etx.time = tx.time
                # TODO compare/replace input/output list
                return True
            return False

        if self._model:
            self._model.beforeAppendTx(tx)
        self._tx_list.append(tx)
        if self._model:
            self._model.afterAppendTx(tx)
        return True
