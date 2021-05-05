# JOK4
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from ...utils.serialize import Serializable, serializable

if TYPE_CHECKING:
    from typing import Any, List, Optional, Tuple
    from .address import AbstractAddress
    from .coin import AbstractCoin


class _AbstractTxIo:
    def __init__(self, address: AbstractAddress) -> None:
        self._address = address

    @property
    def address(self) -> AbstractAddress:
        return self._address


################################################################################
# TODO old code

_UNSPENT_TYPES = {
    # Dictionary containing as keys known unspent types and as value a
    # dictionary containing information if spending uses a witness
    # program (Segwit) and its estimated scriptSig size.

    # Unknown type
    'unknown': {'segwit': None, 'vsize': 180},
    # Legacy P2PKH using uncompressed keys
    'p2pkh-uncompressed': {'segwit': False, 'vsize': 180},
    # Legacy P2PKH
    'p2pkh':   {'segwit': False, 'vsize': 148},
    # Legacy P2SH (vsize corresponds to a 2-of-3 multisig input)
    'p2sh':    {'segwit': False, 'vsize': 292},
    # (Nested) P2SH-P2WKH
    'np2wkh':  {'segwit': True,  'vsize': 90},
    # (Nested) P2SH-P2WSH (vsize corresponds to a 2-of-3 multisig input)
    'np2wsh':  {'segwit': True,  'vsize': 139},
    # Bech32 P2WKH -- Not yet supported to sign
    'p2wpkh':   {'segwit': True,  'vsize': 67},
    # Bech32 P2WSH -- Not yet supported to sign
    'p2wsh':   {'segwit': True,  'vsize': 104}
}
################################################################################


class _AbstractUtxo(Serializable):
    def __init__(
            self,
            address: AbstractAddress,
            *,
            name: str,
            height: int,
            index: int,
            amount: int) -> None:
        super().__init__()
        self._address = address
        self._name = name
        self._height = height
        self._index = index
        self._amount = amount

        # TODO old code
        self.script = None
        self.type = self._address.type.value.name
        self.vsize = _UNSPENT_TYPES[self.type]['vsize']
        self.segwit = _UNSPENT_TYPES[self.type]['segwit']

    # TODO old code
    def __hash__(self) -> int:
        return hash((
            self._amount,
            self._address.name,
            self.script,
            self._name,
            self._index))

    # TODO old code
    def __eq__(self, other: _AbstractUtxo) -> bool:
        return (self._amount == other._amount and
                self._address.name == other._address.name and
                self.script == other.script and
                self._name == other._name and
                self._index == other._index and
                self.segwit == other.segwit)

    @property
    def address(self) -> AbstractAddress:
        return self._address

    @serializable
    @property
    def name(self) -> str:
        return self._name

    @serializable
    @property
    def height(self) -> int:
        return self._height

    @serializable
    @property
    def index(self) -> int:
        return self._index

    @serializable
    @property
    def amount(self) -> int:
        return self._amount


class AbstractTx(Serializable):
    class Status(Enum):
        PENDING = 0
        CONFIRMED = 1
        COMPLETE = 2

    class Interface:
        def __init__(
                self,
                *args,
                tx: AbstractCoin.Tx,
                **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self._tx = tx

        def afterSetHeight(self) -> None:
            raise NotImplementedError

        def afterSetTime(self) -> None:
            raise NotImplementedError

    class Io(_AbstractTxIo):
        pass

    class Utxo(_AbstractUtxo):  # TODO _AbstractUtxo
        pass

    def __init__(
            self,
            address: AbstractAddress,
            *,
            name: str,
            height: int = -1,
            time: int = -1,
            amount: int,
            fee_amount: int,
            coinbase: bool,
            input_list: List[Io],
            output_list: List[Io]) -> None:
        super().__init__()

        self._address = address
        self._name = name.strip().lower()

        self._height = height
        self._time = time
        self._amount = amount
        self._fee_amount = fee_amount
        self._coinbase = coinbase

        self._input_list = input_list
        self._output_list = output_list

        self._model: Optional[AbstractTx.Interface] = \
            self._address.coin.model_factory(self)

    def __eq__(self, other: AbstractTx) -> bool:
        # TODO compare self._input_list, self._output_list
        return self._name == other._name

    def __hash__(self) -> int:
        return hash(self._name)

    @classmethod
    def _deserialize(cls, args: Tuple[Any], key: str, value: Any) -> Any:
        if isinstance(value, dict) and key in ("input_list", "output_list"):
            coin: AbstractCoin = args[0].coin
            address_type = value["address_type"]
            address_name = value["address_name"]
            amount = value["amount"]

            if address_name is None or address_type is None:
                address = coin.Address.createNullData(coin, amount=amount)
            else:
                address = coin.Address.decode(
                    coin,
                    name=address_name,
                    amount=amount)
                if address is None:
                    address = coin.Address.createNullData(
                        coin,
                        name=address_name or "UNKNOWN",
                        amount=amount)
            return cls.Io(address)
        return super()._deserialize(args, key, value)

    @property
    def model(self) -> Optional[AbstractTx.Interface]:
        return self._model

    @property
    def address(self) -> AbstractAddress:
        return self._address

    @serializable
    @property
    def name(self) -> str:
        return self._name

    @serializable
    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        if self._height != value:
            assert self._height == -1
            self._height = value
            if self._model:
                self._model.afterSetHeight()

    @property
    def confirmations(self) -> int:
        if 0 <= self._height <= self._address.coin.height:
            return self._address.coin.height - self._height + 1
        return 0

    @property
    def status(self) -> Status:
        c = self.confirmations
        if c <= 0:
            return self.Status.PENDING
        if c <= 6:  # TODO const
            return self.Status.CONFIRMED
        return self.Status.COMPLETE

    @serializable
    @property
    def time(self) -> int:
        return self._time

    @time.setter
    def time(self, value: int) -> None:
        if self._time != value:
            self._time = value
            if self._model:
                self._model.afterSetTime()

    @serializable
    @property
    def amount(self) -> int:
        return self._amount

    @serializable
    @property
    def feeAmount(self) -> int:
        return self._fee_amount

    @serializable
    @property
    def coinbase(self) -> bool:
        return self._coinbase

    @serializable
    @property
    def inputList(self) -> List[Io]:
        return self._input_list

    @serializable
    @property
    def outputList(self) -> List[Io]:
        return self._output_list
