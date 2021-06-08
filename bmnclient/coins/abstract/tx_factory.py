# JOK4
from __future__ import annotations

import logging
from functools import lru_cache
from itertools import chain
from typing import TYPE_CHECKING

from ..utils import CoinUtils
from ...crypto.secp256k1 import PublicKey
from ...logger import Logger

if TYPE_CHECKING:
    from typing import List, Optional, Sequence, Tuple, Type
    from .coin import AbstractCoin
    SelectedUtxoList = Tuple[List[AbstractCoin.Tx.Utxo], int]


def _safeScriptIntegerToBytes(
        script_type: Type[AbstractCoin.Script],
        value: int,
        length: int) -> bytes:
    value = script_type.integerToBytes(value, length)
    return value if not None else (b"\x00" * length)


class _AbstractMutableTxIo:
    _AMOUNT_LENGTH = 0

    def __init__(
            self,
            coin: AbstractCoin,
            amount: int,
            *,
            is_dummy: bool = False):
        assert amount >= 0
        self._is_dummy = is_dummy
        self._coin = coin
        self._amount = amount
        self._script_bytes = b""

    @property
    def isDummy(self) -> bool:
        return self._is_dummy

    @property
    def amount(self) -> int:
        return self._amount

    @property
    def amountBytes(self) -> bytes:
        return _safeScriptIntegerToBytes(
            self._coin.Script,
            self._amount,
            self._AMOUNT_LENGTH)

    @property
    def scriptBytes(self) -> bytes:
        return self._script_bytes


class _AbstractMutableTxInput(_AbstractMutableTxIo):
    _HASH_TYPE_LENGTH = 0
    _SEQUENCE_LENGTH = 0

    def __init__(
            self,
            utxo: AbstractCoin.Tx.Utxo,
            *,
            utxo_id_bytes: bytes,
            hash_type: int,
            sequence: int,
            **kwargs) -> None:
        super().__init__(utxo.coin, utxo.amount, **kwargs)
        self._utxo = utxo
        self._utxo_id_bytes = utxo_id_bytes
        self._hash_type = hash_type
        self._sequence = sequence

        self._script_sig_bytes = b""
        self._witness_bytes = b""

    def __eq__(self, other: AbstractCoin.TxFactory.MutableTx.Input):
        return (
                isinstance(other, self.__class__)
                and self._utxo_id_bytes == other._utxo_id_bytes
        )

    def __hash__(self) -> int:
        return hash((self._utxo_id_bytes, ))

    @property
    def isWitness(self) -> bool:
        return self._utxo.address.type.value.isWitness

    @property
    def utxo(self) -> AbstractCoin.Tx.Utxo:
        return self._utxo

    @property
    def utxoIdBytes(self) -> bytes:
        return self._utxo_id_bytes

    @property
    def hashType(self) -> int:
        return self._hash_type

    @property
    def hashTypeBytes(self) -> bytes:
        return _safeScriptIntegerToBytes(
            self._coin.Script,
            self._hash_type,
            self._HASH_TYPE_LENGTH)

    @property
    def sequence(self) -> int:
        return self._sequence

    @property
    def sequenceBytes(self) -> bytes:
        return _safeScriptIntegerToBytes(
            self._coin.Script,
            self._sequence,
            self._SEQUENCE_LENGTH)

    @property
    def scriptSigBytes(self) -> bytes:
        return self._script_sig_bytes

    @property
    def witnessBytes(self) -> bytes:
        return self._witness_bytes

    def sign(self, hash_: bytes) -> bool:
        raise NotImplementedError


class _AbstractMutableTxOutput(_AbstractMutableTxIo):
    def __init__(
            self,
            address: AbstractCoin.Address,
            amount: int,
            **kwargs) -> None:
        super().__init__(address.coin, amount, **kwargs)
        self._address = address


class _AbstractMutableTx:
    _VERSION_LENGTH = 0
    _LOCK_TIME_LENGTH = 0

    Input = _AbstractMutableTxInput
    Output = _AbstractMutableTxOutput

    def __init__(
            self,
            coin: AbstractCoin,
            input_list: Sequence[Input],
            output_list: Sequence[Output],
            *,
            version: int,
            lock_time: int,
            is_dummy: bool = False):
        self._is_dummy = is_dummy
        self._coin = coin
        self._input_list = input_list
        self._output_list = output_list
        self._version = version
        self._lock_time = lock_time
        self._is_witness = any(i.isWitness for i in self._input_list)
        self._is_signed = False

    @property
    def isDummy(self) -> bool:
        return self._is_dummy

    def _deriveName(self) -> Optional[str]:
        raise NotImplementedError

    @property
    @lru_cache
    def name(self) -> Optional[str]:
        if not self._is_signed or self._is_dummy:
            return None
        return self._deriveName()

    @property
    def coin(self) -> AbstractCoin:
        return self._coin

    @property
    def version(self) -> int:
        return self._version

    @property
    def versionBytes(self) -> bytes:
        return _safeScriptIntegerToBytes(
            self._coin.Script,
            self._version,
            self._VERSION_LENGTH)

    @property
    def lockTime(self) -> int:
        return self._lock_time

    @property
    def lockTimeBytes(self) -> bytes:
        return _safeScriptIntegerToBytes(
            self._coin.Script,
            self._lock_time,
            self._LOCK_TIME_LENGTH)

    @property
    def isWitness(self) -> bool:
        return self._is_witness

    @property
    def isSigned(self) -> bool:
        return self._is_signed

    def _sign(self) -> bool:
        raise NotImplementedError

    def sign(self) -> bool:
        self.__class__.serialize.cache_clear()
        self.__class__.name.fget.cache_clear()
        if not self._is_signed and self._sign():
            self._is_signed = True
            return True
        return False

    def _serialize(self, *, with_witness: bool = True, **kwargs) -> bytes:
        raise NotImplementedError

    @lru_cache
    def serialize(self, *, with_witness: bool = True, **kwargs) -> bytes:
        if not self._is_signed:
            return b""
        return self._serialize(with_witness=with_witness, **kwargs)

    @property
    def rawSize(self) -> int:
        return len(self.serialize(with_witness=True))

    @property
    def virtualSize(self) -> int:
        raise NotImplementedError


class _AbstractTxFactoryInterface:
    def __init__(
            self,
            *args,
            factory: AbstractCoin.TxFactory,
            **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._factory = factory

    def afterUpdateReceiverAmount(self) -> None:
        raise NotImplementedError

    def afterUpdateChangeAmount(self) -> None:
        raise NotImplementedError

    def afterUpdateFeeAmount(self) -> None:
        raise NotImplementedError

    def onBroadcast(self, mtx: AbstractCoin.TxFactory.MutableTx) -> None:
        raise NotImplementedError


class _AbstractTxFactory:
    Interface = _AbstractTxFactoryInterface
    MutableTx = _AbstractMutableTx

    class _SelectedUtxoData:
        __slots__ = ("list", "amount", "raw_size", "virtual_size")

        def __init__(self) -> None:
            self.list: List[AbstractCoin.Tx.Utxo] = []
            self.amount = 0
            self.raw_size = -1
            self.virtual_size = -1

    def __init__(self, coin: AbstractCoin) -> None:
        self._logger = Logger.classLogger(
            self.__class__,
            *CoinUtils.coinToNameKeyTuple(coin))
        self._coin = coin

        self._utxo_list: List[AbstractCoin.Tx.Utxo] = []
        self._utxo_amount = 0
        self._selected_utxo_data = self._SelectedUtxoData()

        self._receiver_address: Optional[AbstractCoin.Address] = None
        self._receiver_amount = 0

        self._change_address: Optional[AbstractCoin.Address] = None

        self._subtract_fee = False
        self._fee_amount_per_byte = 103  # TODO

        self._dummy_change_address = self._createDummyChangeAddress()

        self._mtx: Optional[AbstractCoin.TxFactory.MutableTx] = None

        self._model: Optional[AbstractCoin.TxFactory.Interface] = \
            self._coin.model_factory(self)

    def _createDummyChangeAddress(self) -> Optional[AbstractCoin.Address]:
        public_key = PublicKey.fromPublicInteger(
            1,
            None,
            is_compressed=True)
        if public_key is None:
            self._logger.error("Failed to derive dummy change public key.")
            return None

        address = self._coin.Address.create(
                self._coin,
                type_=self._coin.Address.Type.DEFAULT,
                key=public_key
            )
        if address is None:
            self._logger.error("Failed to derive dummy change address.")
        else:
            self._logger.error("Dummy change address: %s", address.name)
        return address

    @property
    def model(self) -> Optional[AbstractCoin.TxFactory.Interface]:
        return self._model

    @property
    def coin(self) -> AbstractCoin:
        return self._coin

    @property
    def name(self) -> Optional[str]:
        if self._mtx is not None:
            return self._mtx.name
        return None

    def setReceiverAddressName(self, name: str) -> bool:
        if not name:
            self._receiver_address = None
        else:
            self._receiver_address = self._coin.Address.decode(
                self._coin,
                name=name)
        self._selectUtxoList()

        if self._receiver_address is None:
            self._logger.warning(
                "Receiver address '%s' is invalid.",
                name)
            return False
        else:
            self._logger.debug(
                "Receiver address: %s",
                self._receiver_address.name)
            return True

    @property
    def receiverAddress(self) -> Optional[AbstractCoin.Address]:
        return self._receiver_address

    @property
    def changeAddress(self) -> Optional[AbstractCoin.Address]:
        return self._change_address

    @property
    def availableAmount(self) -> int:
        return self._utxo_amount

    @property
    def receiverAmount(self) -> int:
        return self._receiver_amount

    @receiverAmount.setter
    def receiverAmount(self, value: int) -> None:
        if self._receiver_amount != value:
            self._receiver_amount = value
            self._selectUtxoList()
            if self._model:
                self._model.afterUpdateReceiverAmount()

    def setReceiverMaxAmount(self) -> int:
        if self._selectUtxoList(select_all=True):
            value = self._selected_utxo_data.amount
            if not self._subtract_fee:
                value -= self.feeAmount
            value = max(value, 0)
        else:
            value = 0

        if self._receiver_amount != value:
            self._receiver_amount = value
            if self._model:
                self._model.afterUpdateReceiverAmount()

        return value

    @property
    def isValidReceiverAmount(self) -> bool:
        return 0 <= self._receiver_amount and self.changeAmount >= 0

    @property
    def subtractFee(self) -> bool:
        return self._subtract_fee

    @subtractFee.setter
    def subtractFee(self, value: bool) -> None:
        if self._subtract_fee != value:
            self._subtract_fee = value
            self._selectUtxoList()

    @property
    def feeAmountPerByteDefault(self) -> int:
        # TODO
        return 103

    @property
    def feeAmountPerByte(self) -> int:
        return self._fee_amount_per_byte

    @feeAmountPerByte.setter
    def feeAmountPerByte(self, value: int) -> None:
        if self._fee_amount_per_byte != value:
            self._fee_amount_per_byte = value
            self._selectUtxoList()

    @property
    def feeAmountDefault(self) -> int:
        return self._feeAmount(
            self.feeAmountPerByteDefault,
            self._selected_utxo_data.raw_size,
            self._selected_utxo_data.virtual_size)

    @property
    def feeAmount(self) -> int:
        return self._feeAmount(
            self._fee_amount_per_byte,
            self._selected_utxo_data.raw_size,
            self._selected_utxo_data.virtual_size)

    @property
    def isValidFeeAmount(self) -> bool:
        fee_amount = self.feeAmount
        if fee_amount < 0:
            return False
        if self._subtract_fee and fee_amount > self._receiver_amount:
            return False
        return self.changeAmount >= 0

    @property
    def changeAmount(self) -> int:
        change_amount = self._selected_utxo_data.amount - self._receiver_amount
        if not self._subtract_fee:
            change_amount -= self.feeAmount
        return change_amount

    def clear(self) -> None:
        self._change_address = None
        self._mtx = None

    @classmethod
    def _feeAmount(
            cls,
            amount_per_byte: int,
            raw_size: int,  # noqa
            virtual_size: int) -> int:
        if virtual_size > 0:
            return amount_per_byte * virtual_size
        return 0

    def _prepare(
            self,
            input_list: Sequence[AbstractCoin.Tx.Utxo],
            output_list: Sequence[Tuple[AbstractCoin.Address, int]],
            *,
            is_dummy: bool) \
            -> Optional[AbstractCoin.TxFactory.MutableTx]:
        raise NotImplementedError

    def prepare(self) -> bool:
        if not self.isValidReceiverAmount:
            self._logger.error(
                "Invalid receiver amount: %i",
                self._receiver_amount)
            return False

        if not self.isValidFeeAmount:
            self._logger.error("Invalid fee amount: %i", self.feeAmount)
            return False

        if not self._selected_utxo_data.list:
            self._logger.error("No input UTXO's selected.")
            return False

        change_amount = self.changeAmount
        receiver_amount = self._receiver_amount
        if self._subtract_fee:
            receiver_amount -= self.feeAmount

        output_list = [(self._receiver_address, receiver_amount)]

        if change_amount > 0:
            self._change_address = self._coin.deriveHdAddress(
                account=0,
                is_change=True)
            if self._change_address is None:
                self._logger.error("Failed to derive change address.")
                return False
            output_list.append((self._change_address, change_amount))
        else:
            self._change_address = None

        self._mtx = self._prepare(
            self._selected_utxo_data.list,
            output_list,
            is_dummy=False)
        return self._mtx is not None

    def sign(self) -> bool:
        if self._mtx is None or not self._mtx.sign():
            return False
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug(
                "Signed transaction: %s",
                self._mtx.serialize().hex())
        return True

    def broadcast(self) -> bool:
        if self._mtx is None or not self._mtx.isSigned:
            return False
        if self._change_address is not None:
            self._coin.appendAddress(self._change_address)
        mtx = self._mtx

        self.clear()
        if self._model:
            self._model.onBroadcast(mtx)
        return True

    @staticmethod
    def _newUtxoIsBest(
            old_utxo: Optional[AbstractCoin.Tx.Utxo],
            new_utxo: AbstractCoin.Tx.Utxo) -> bool:
        return old_utxo is None or new_utxo.height < old_utxo.height

    @classmethod
    def _findExactUtxo(
            cls,
            utxo_list: Sequence[AbstractCoin.Tx.Utxo],
            target_amount: int) -> Optional[AbstractCoin.Tx.Utxo]:
        exact_utxo = None
        for utxo in utxo_list:
            if utxo.amount == target_amount:
                if cls._newUtxoIsBest(exact_utxo, utxo):
                    exact_utxo = utxo
        return exact_utxo

    @classmethod
    def _findOptimalUtxoList(
            cls,
            utxo_list: Sequence[AbstractCoin.Tx.Utxo],
            target_amount: int) -> SelectedUtxoList:
        # single utxo
        exact_utxo = None
        for utxo in utxo_list:
            if utxo.amount >= target_amount:
                if (
                        exact_utxo is None
                        or (utxo.amount < exact_utxo.amount)
                        or (
                            exact_utxo.amount == utxo.amount
                            and cls._newUtxoIsBest(exact_utxo, utxo)
                        )
                ):
                    exact_utxo = utxo
        if exact_utxo is not None:
            return [exact_utxo], exact_utxo.amount

        return cls._findOptimalUtxoListStrategy1(utxo_list, target_amount)

    @staticmethod
    def _findOptimalUtxoListStrategy1(
            utxo_list: Sequence[AbstractCoin.Tx.Utxo],
            target_amount: int) -> SelectedUtxoList:
        if len(utxo_list) < 2:
            return [], 0

        best_utxo_list = []
        best_utxo_amount = 0
        utxo_list_offset = 0
        utxo_list = sorted(
            utxo_list,
            key=lambda u: (u.amount, u.height),
            reverse=True)

        for limit in range(2, len(utxo_list) + 1):
            exact_found = False
            while utxo_list_offset + limit <= len(utxo_list):
                current_list = []
                current_amount = 0
                for i in range(limit):
                    utxo = utxo_list[utxo_list_offset + i]
                    current_list.append(utxo)
                    current_amount += utxo.amount

                if current_amount < target_amount:
                    break
                if current_amount == target_amount:
                    exact_found = True
                elif exact_found:
                    break

                best_utxo_list = current_list
                best_utxo_amount = current_amount
                utxo_list_offset += 1

            if best_utxo_list:
                break

        return best_utxo_list, best_utxo_amount

    @classmethod
    def _findUtxoList(
            cls,
            utxo_list: Sequence[AbstractCoin.Tx.Utxo],
            target_amount: int) -> SelectedUtxoList:
        if target_amount <= 0:
            return [], 0

        exact_utxo = cls._findExactUtxo(utxo_list, target_amount)
        if exact_utxo is not None:
            return [exact_utxo], exact_utxo.amount
        else:
            return cls._findOptimalUtxoList(utxo_list, target_amount)

    def _calcEstimatedSizes(
            self,
            utxo_list: Sequence[AbstractCoin.Tx.Utxo],
            utxo_amount: int) -> Tuple[int, int]:
        if not utxo_list or self._receiver_address is None:
            print("E1")
            return -1, -1

        max_amount = self._coin.Currency.maxValue
        output_list = [(self._receiver_address, max_amount)]
        if utxo_amount != self._receiver_amount or not self._subtract_fee:
            if self._dummy_change_address is not None:
                output_list.append((self._dummy_change_address, max_amount))

        mtx = self._prepare(utxo_list, output_list, is_dummy=True)
        if mtx is None or not mtx.sign():
            print("E2")
            return -1, -1
        else:
            return mtx.rawSize, mtx.virtualSize

    def _selectUtxoList(self, *, select_all: bool = False) -> bool:
        self._selected_utxo_data = self._SelectedUtxoData()

        if select_all:
            raw_size, virtual_size = self._calcEstimatedSizes(
                self._utxo_list,
                self._utxo_amount)
            self._selected_utxo_data.list = self._utxo_list
            self._selected_utxo_data.amount = self._utxo_amount
            self._selected_utxo_data.raw_size = raw_size
            self._selected_utxo_data.virtual_size = virtual_size
            return raw_size >= 0

        fee_amount = 0
        while True:
            full_amount = self._receiver_amount + fee_amount
            if not full_amount:
                full_amount = 1
            utxo_list, utxo_amount = self._findUtxoList(
                self._utxo_list,
                full_amount)
            raw_size, virtual_size = self._calcEstimatedSizes(
                utxo_list,
                utxo_amount)
            if raw_size <= 0:
                print("SSS INVALID", raw_size, virtual_size)
                assert raw_size == virtual_size
                break
            if self._subtract_fee:
                print("SSS SUB")
                break

            new_fee_amount = self._feeAmount(
                self._fee_amount_per_byte,
                raw_size,
                virtual_size)
            if fee_amount == new_fee_amount:
                print("SSS OK", fee_amount, new_fee_amount)
                break
            print("SSS NEXT", fee_amount, new_fee_amount)
            fee_amount = new_fee_amount

        self._selected_utxo_data.list = utxo_list
        self._selected_utxo_data.amount = utxo_amount
        self._selected_utxo_data.raw_size = raw_size
        self._selected_utxo_data.virtual_size = virtual_size
        return raw_size >= 0

    def updateUtxoList(self) -> None:
        address_filter = dict(is_read_only=False, with_utxo=True)

        self._utxo_list = list(chain.from_iterable(
            a.utxoList
            for a in self._coin.filterAddressList(**address_filter)))
        self._utxo_amount = sum(u.amount for u in self._utxo_list)

        if self._logger.isEnabledFor(logging.DEBUG):
            s = "".join("\n\t" + str(u) for u in self._utxo_list)
            self._logger.debug(
                "Available UTXO's:%s\n\ttotal amount: %i",
                s if s else "\n\tNone",
                self._utxo_amount)

        self._selectUtxoList()
