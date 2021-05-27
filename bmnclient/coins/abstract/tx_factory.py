# JOK4
from __future__ import annotations

import logging
from itertools import chain
from typing import TYPE_CHECKING

from ..utils import CoinUtils
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
    def isSegwit(self) -> bool:
        return self._utxo.address.type.value.isSegwit

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
        self._is_segwit = any(i.isSegwit for i in self._input_list)
        self._is_signed = False

    @property
    def isDummy(self) -> bool:
        return self._is_dummy

    @property
    def name(self) -> str:
        raise NotImplementedError

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
    def isSegwit(self) -> bool:
        return self._is_segwit

    @property
    def isSigned(self) -> bool:
        return self._is_signed

    def _sign(self) -> bool:
        raise NotImplementedError

    def sign(self) -> bool:
        if not self._is_signed and self._sign():
            self._is_signed = True
            return True
        return False

    def serialize(self, *, with_segwit: bool = True) -> bytes:
        raise NotImplementedError


class _AbstractTxFactoryInterface:
    def __init__(
            self,
            *args,
            factory: AbstractCoin.TxFactory,
            **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._factory = factory

    def afterUpdateAvailableAmount(self) -> None:
        raise NotImplementedError

    def onBroadcast(self, mtx: AbstractCoin.TxFactory.MutableTx) -> None:
        raise NotImplementedError


class _AbstractTxFactory:
    Interface = _AbstractTxFactoryInterface
    MutableTx = _AbstractMutableTx

    def __init__(self, coin: AbstractCoin) -> None:
        self._logger = Logger.classLogger(
            self.__class__,
            *CoinUtils.coinToNameKeyTuple(coin))
        self._coin = coin

        self._receiver_address: Optional[AbstractCoin.Address] = None
        self._receiver_amount = 0
        self._change_address: Optional[AbstractCoin.Address] = None

        self._available_amount = 0
        self._subtract_fee = False
        self._fee_amount_per_byte = 103  # TODO

        self._selected_utxo_list: List[AbstractCoin.Tx.Utxo] = []
        self._selected_utxo_list_amount = 0

        self._mtx: Optional[AbstractCoin.TxFactory.MutableTx] = None

        self._model: Optional[AbstractCoin.TxFactory.Interface] = \
            self._coin.model_factory(self)

    @property
    def model(self) -> Optional[AbstractCoin.TxFactory.Interface]:
        return self._model

    @property
    def coin(self) -> AbstractCoin:
        return self._coin

    @property
    def name(self) -> Optional[str]:
        if self.__mtx is not None:
            return self.__mtx.name
        return None

    def setReceiverAddressName(self, name: str) -> bool:
        self._receiver_address = self._coin.Address.decode(
            self._coin,
            name=name)
        if self._receiver_address is None:
            self._logger.warning(
                "Receiver address '%s' is invalid.",
                name)
            return False
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

    def refreshUtxoList(self) -> None:
        self.updateUtxoList()

    @property
    def availableAmount(self) -> int:
        return self._available_amount

    @property
    def receiverAmount(self) -> int:
        return self._receiver_amount

    @receiverAmount.setter
    def receiverAmount(self, value: int) -> None:
        if self._receiver_amount != value:
            self._receiver_amount = value
            self.updateUtxoList()

            self._logger.debug(
                "Receiver amount: %i, available: %i, change %i",
                self._receiver_amount,
                self._available_amount,
                self.changeAmount)

    @property
    def maxReceiverAmount(self) -> int:
        amount = self._available_amount
        if not self._subtract_fee:
            amount -= self.feeAmount
        return max(amount, 0)

    @property
    def isValidReceiverAmount(self) -> bool:
        if (
                0 <= self._receiver_amount <= self.maxReceiverAmount
                and self.changeAmount >= 0
        ):
            return True
        return False

    @property
    def subtractFee(self) -> bool:
        return self._subtract_fee

    @subtractFee.setter
    def subtractFee(self, value: bool) -> None:
        if self._subtract_fee != value:
            self._subtract_fee = value
            self.updateUtxoList()

    @property
    def feeAmountPerByteDefault(self) -> int:
        return 103  # TODO

    @property
    def feeAmountPerByte(self) -> int:
        return self._fee_amount_per_byte

    @feeAmountPerByte.setter
    def feeAmountPerByte(self, value: int) -> None:
        if self._fee_amount_per_byte != value:
            self._fee_amount_per_byte = value
            self.updateUtxoList()

    @property
    def feeAmountDefault(self) -> int:
        return self.feeAmountPerByteDefault * self.tx_size

    @property
    def feeAmount(self) -> int:
        return self.feeAmountPerByte * self.tx_size

    @feeAmount.setter
    def feeAmount(self, value: int):
        self.feeAmountPerByte = value // self.tx_size

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
        change_amount = self._selected_utxo_list_amount - self._receiver_amount
        if not self._subtract_fee:
            change_amount -= self.feeAmount
        return change_amount

    def clear(self) -> None:
        # TODO
        pass

    def prepare(self) -> bool:
        if not self.isValidReceiverAmount:
            self._logger.error(
                "Invalid receiver amount: %i",
                self._receiver_amount)
            return False

        if not self.isValidFeeAmount:
            self._logger.error("Invalid fee amount: %i", self.feeAmount)
            return False

        if not self._selected_utxo_list:
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
            # TODO validate hd node private key
            assert self._change_address is not None
            output_list.append((self._change_address, change_amount))
        else:
            self._change_address = None

        self.__mtx = Mtx.make(self._coin, self._selected_utxo_list, output_list)
        return True

    def sign(self) -> bool:
        if self.__mtx is None:
            return False

        # TODO Dict[str, ...]?
        source_list: Dict[AbstractCoin.Address, List[AbstractCoin.Tx.Utxo]] = {}
        for utxo in self._selected_utxo_list:
            source_list.setdefault(utxo.address, []).append(utxo)

        for address, utxo_list in source_list.items():
            if self._logger.isEnabledFor(logging.DEBUG):
                for utxo in utxo_list:
                    self._logger.debug(
                        "Input: %s, UTXO '%s':%i, amount %i.",
                        address.name,
                        utxo.name,
                        utxo.index,
                        utxo.amount)
            self.__mtx.sign(address, utxo_list=utxo_list)

        self.__mtx_result = self.__mtx.serialize().hex()
        if not self.__mtx_result:
            return False
        self._logger.debug(f"Signed transaction: %s", self.__mtx_result)
        if self._change_address is not None:
            self._coin.appendAddress(self._change_address)
        return True

    def broadcast(self) -> bool:
        if self._mtx is None or not self._mtx.isSigned:
            return False
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

    @classmethod
    def _findOptimalUtxoListStrategy1(
            cls,
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

    def updateUtxoList(self) -> None:
        address_filter = dict(is_read_only=False, with_utxo=True)

        # calc available amount
        available_amount = 0
        for address in self._coin.filterAddressList(**address_filter):
            for utxo in address.utxoList:
                available_amount += utxo.amount
        if self._available_amount != available_amount:
            self._available_amount = available_amount
            if self._model:
                self._model.afterUpdateAvailableAmount()

        # clean selected utxo's
        self._selected_utxo_list = []
        self._selected_utxo_list_amount = 0

        target_amount = self._receiver_amount
        if not self._subtract_fee:
            target_amount += self.feeAmount
        if target_amount <= 0:
            if target_amount < 0:
                self._logger.warning("Amount is negative (%i).", target_amount)
            return

        # try find exact utxo
        exact_utxo = None
        for address in self._coin.filterAddressList(**address_filter):
            utxo = self._findExactUtxo(address.utxoList, target_amount)
            if utxo is not None:
                if self._newUtxoIsBest(exact_utxo, utxo):
                    exact_utxo = utxo
        if exact_utxo is not None:
            assert exact_utxo.amount == target_amount
            self._logger.debug("Selected exact UTXO '%s'", str(exact_utxo))
            self._selected_utxo_list = [exact_utxo]
            self._selected_utxo_list_amount = exact_utxo.amount
            return

        # combine all utxo's
        utxo_list = list(chain.from_iterable(map(
            lambda a: a.utxoList,
            self._coin.filterAddressList(**address_filter))))
        if self._logger.isEnabledFor(logging.DEBUG):
            s = "".join("\n\t" + str(u) for u in utxo_list)
            self._logger.debug("Available UTXO's:%s", s if s else " None")

        utxo_list, utxo_amount = self._findOptimalUtxoList(
            utxo_list,
            target_amount)
        if self._logger.isEnabledFor(logging.DEBUG):
            s = "".join("\n\t" + str(u) for u in utxo_list)
            self._logger.debug("Selected UTXO's:%s", s if s else " None")

        self._selected_utxo_list = utxo_list
        self._selected_utxo_list_amount = utxo_amount

    # TODO wrong code
    # https://murchandamus.medium.com/psa-wrong-fee-rates-on-block-explorers-48390cbfcc74
    # https://jlopp.github.io/bitcoin-transaction-size-calculator/
    @property
    def tx_size(self) -> int:
        n_in = max(1, len(self._selected_utxo_list))
        n_out = 2 if self._selected_utxo_list_amount > self._receiver_amount else 1
        return (
                150
                + len(self._coin.Script.integerToAutoBytes(n_in))
                + 70
                + len(self._coin.Script.integerToAutoBytes(n_out))
                + 8
        )
