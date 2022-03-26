from __future__ import annotations

import logging
from itertools import chain
from time import time
from typing import TYPE_CHECKING

from .object import CoinObject, CoinObjectModel
from ..utils import CoinUtils
from ...crypto.secp256k1 import PublicKey
from ...logger import Logger

if TYPE_CHECKING:
    from typing import List, Optional, Sequence, Tuple
    from .coin import Coin
    SelectedUtxoList = Tuple[List[Coin.Tx.Utxo], int]


class _Model(CoinObjectModel):
    def __init__(
            self,
            *args,
            factory: Coin.TxFactory,
            **kwargs) -> None:
        super().__init__(
            *args,
            name_key_tuple=CoinUtils.txFactoryToNameKeyTuple(factory),
            **kwargs)
        self._factory = factory

    @property
    def owner(self) -> Coin.TxFactory:
        return self._factory

    def afterUpdateState(self) -> None: pass
    def afterSetInputAddress(self) -> None: pass
    def afterSetReceiverAddress(self) -> None: pass
    def onBroadcast(self, mtx: Coin.TxFactory.MutableTx) -> None: pass


class _TxFactory(CoinObject, table_type=None):
    Model = _Model

    from .mutable_tx import _MutableTx
    MutableTx = _MutableTx

    class _SelectedUtxoData:
        __slots__ = ("list", "amount", "raw_size", "virtual_size")

        def __init__(self) -> None:
            self.list: List[Coin.Tx.Utxo] = []
            self.amount = 0
            self.raw_size = -1
            self.virtual_size = -1

    def __init__(self, coin: Coin) -> None:
        super().__init__(coin)
        self._logger = Logger.classLogger(
            self.__class__,
            *CoinUtils.coinToNameKeyTuple(coin))

        self._utxo_list: Sequence[Coin.Tx.Utxo] = []
        self._utxo_amount = 0
        self._selected_utxo_data = self._SelectedUtxoData()

        self._input_address: Optional[Coin.Address] = None

        self._receiver_address: Optional[Coin.Address] = None
        self._receiver_amount = 0

        self._change_address: Optional[Coin.Address] = None

        self._subtract_fee = False
        self._fee_amount_per_byte = 103  # TODO

        self._dummy_change_address: Optional[Coin.Address] = None

        self._mtx: Optional[_TxFactory.MutableTx] = None

    def _createDummyChangeAddress(self) -> Optional[Coin.Address]:
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
            self._logger.debug("Dummy change address: %s", address.name)
        return address

    @property
    def name(self) -> Optional[str]:
        if self._mtx is not None:
            return self._mtx.name
        return None

    @property
    def inputAddress(self) -> Optional[Coin.Address]:
        return self._input_address

    def setInputAddressName(self, name: Optional[str]) -> bool:
        result = True

        if name is None:
            address = None
            self._logger.debug("Input address: *")
        else:
            address = self._coin.Address.createFromName(self._coin, name=name)
            if address is not None:
                self._logger.debug("Input address: %s", address.name)
            else:
                self._logger.warning("Input address '%s' is invalid.", name)
                result = False

        if self._input_address == address:
            return result

        self._coin.setTxInputAddress(address)
        self._input_address = address
        self._callModel("afterSetInputAddress")
        self.updateUtxoList()

        return result

    def setReceiverAddressName(self, name: str) -> bool:
        if not name:
            address = None
        else:
            address = self._coin.Address.createFromName(self._coin, name=name)

        if address is None:
            self._logger.warning("Receiver address '%s' is invalid.", name)
        else:
            self._logger.debug("Receiver address: %s", address.name)

        if self._receiver_address != address:
            self._receiver_address = address
            self._callModel("afterSetReceiverAddress")
            self._selectUtxoList()

        return address is not None

    @property
    def receiverAddress(self) -> Optional[Coin.Address]:
        return self._receiver_address

    @property
    def changeAddress(self) -> Optional[Coin.Address]:
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

    def setReceiverMaxAmount(self) -> int:
        if self._selectUtxoList(select_all=True, skip_model_update=True):
            value = self._selected_utxo_data.amount
            if not self._subtract_fee:
                fee_amount = self.feeAmount
                if fee_amount is not None:
                    value -= fee_amount
            value = max(value, 0)
        else:
            value = 0

        self._receiver_amount = value
        self._callModel("afterUpdateState")
        return value

    @property
    def isValidReceiverAmount(self) -> bool:
        return bool(self._receiver_amount >= 0 and self.isValidChangeAmount)

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
    def feeAmount(self) -> Optional[int]:
        return self._feeAmount(
            self._fee_amount_per_byte,
            self._selected_utxo_data.raw_size,
            self._selected_utxo_data.virtual_size)

    @property
    def isValidFeeAmount(self) -> bool:
        fee_amount = self.feeAmount
        if fee_amount is None or fee_amount < 0:
            return False
        if self._subtract_fee and fee_amount > self._receiver_amount:
            return False
        return self.isValidChangeAmount

    @property
    def changeAmount(self) -> Optional[int]:
        change_amount = self._selected_utxo_data.amount - self._receiver_amount
        if not self._subtract_fee:
            fee_amount = self.feeAmount
            if fee_amount is None:
                return None
            change_amount -= fee_amount
        return change_amount if change_amount >= 0 else None

    @property
    def isValidChangeAmount(self) -> bool:
        return self.changeAmount is not None

    @property
    def estimatedRawSize(self) -> int:
        return self._selected_utxo_data.raw_size

    @property
    def estimatedVirtualSize(self) -> int:
        return self._selected_utxo_data.virtual_size

    def clear(self) -> None:
        self._change_address = None
        self._mtx = None

    @classmethod
    def _feeAmount(
            cls,
            amount_per_byte: int,
            raw_size: int,  # noqa
            virtual_size: int) -> Optional[int]:
        if virtual_size <= 0:
            return None
        return amount_per_byte * virtual_size

    def _prepare(
            self,
            input_list: Sequence[Coin.Tx.Utxo],
            output_list: Sequence[Tuple[Coin.Address, int]],
            *,
            is_dummy: bool) -> Optional[_TxFactory.MutableTx]:
        raise NotImplementedError

    def prepare(self) -> bool:
        if not self._selected_utxo_data.list:
            self._logger.error("No input UTXO's selected.")
            return False

        if not self.isValidChangeAmount:
            self._logger.error(
                "Invalid change amount: %s",
                str(self.changeAmount))
            return False
        change_amount = self.changeAmount

        if not self.isValidReceiverAmount:
            self._logger.error(
                "Invalid receiver amount: %s",
                str(self.receiverAmount))
            return False
        receiver_amount = self.receiverAmount

        if not self.isValidFeeAmount:
            self._logger.error(
                "Invalid fee amount: %s",
                str(self.feeAmount))
            return False
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
            is_dummy=False,
            time=int(time()))
        return self._mtx is not None

    def sign(self) -> bool:
        if self._mtx is None or not self._mtx.sign():
            return False
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug(
                "Signed transaction: %s",
                self._mtx.raw().hex())
        return True

    def broadcast(self) -> bool:
        if self._mtx is None or not self._mtx.isSigned:
            return False
        if self._change_address is not None:
            self._coin.appendAddress(self._change_address)

        mtx = self._mtx

        self.clear()
        self._callModel("onBroadcast", mtx)
        return True

    @staticmethod
    def _newUtxoIsBest(
            old_utxo: Optional[Coin.Tx.Utxo],
            new_utxo: Coin.Tx.Utxo) -> bool:
        return bool(old_utxo is None or new_utxo.height < old_utxo.height)

    @classmethod
    def _findExactUtxo(
            cls,
            utxo_list: Sequence[Coin.Tx.Utxo],
            target_amount: int) -> Optional[Coin.Tx.Utxo]:
        exact_utxo = None
        for utxo in utxo_list:
            if utxo.amount == target_amount:
                if cls._newUtxoIsBest(exact_utxo, utxo):
                    exact_utxo = utxo
        return exact_utxo

    @classmethod
    def _findOptimalUtxoList(
            cls,
            utxo_list: Sequence[Coin.Tx.Utxo],
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
            utxo_list: Sequence[Coin.Tx.Utxo],
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
            utxo_list: Sequence[Coin.Tx.Utxo],
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
            utxo_list: Sequence[Coin.Tx.Utxo],
            utxo_amount: int) -> Tuple[int, int]:
        if not utxo_list or self._receiver_address is None:
            return -1, -1

        output_list = [(self._receiver_address, self._receiver_amount)]
        if utxo_amount != self._receiver_amount or not self._subtract_fee:
            if not self._dummy_change_address:
                self._dummy_change_address = self._createDummyChangeAddress()
            if self._dummy_change_address:
                output_list.append((
                    self._dummy_change_address,
                    self._coin.Currency.maxValue))

        mtx = self._prepare(
            utxo_list,
            output_list,
            is_dummy=True,
            time=int(time()))
        if mtx is None or not mtx.sign():
            return -1, -1
        else:
            return mtx.rawSize, mtx.virtualSize

    def _selectUtxoList(
            self,
            *,
            select_all: bool = False,
            skip_model_update: bool = False) -> bool:
        self._selected_utxo_data = self._SelectedUtxoData()

        if select_all:
            raw_size, virtual_size = self._calcEstimatedSizes(
                self._utxo_list,
                self._utxo_amount)
            self._selected_utxo_data.list = self._utxo_list
            self._selected_utxo_data.amount = self._utxo_amount
            self._selected_utxo_data.raw_size = raw_size
            self._selected_utxo_data.virtual_size = virtual_size

            self.__logUtxoList(
                "Selected UTXO's",
                self._utxo_list,
                self._utxo_amount)
            if not skip_model_update:
                self._callModel("afterUpdateState")
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
                assert raw_size == virtual_size
                break
            if self._subtract_fee:
                break

            new_fee_amount = self._feeAmount(
                self._fee_amount_per_byte,
                raw_size,
                virtual_size)
            if new_fee_amount is None:
                break
            if fee_amount == new_fee_amount:
                break
            fee_amount = new_fee_amount

        self._selected_utxo_data.list = utxo_list
        self._selected_utxo_data.amount = utxo_amount
        self._selected_utxo_data.raw_size = raw_size
        self._selected_utxo_data.virtual_size = virtual_size

        self.__logUtxoList(
            "Selected UTXO's",
            utxo_list,
            utxo_amount)
        if not skip_model_update:
            self._callModel("afterUpdateState")
        return raw_size >= 0

    def updateUtxoList(self) -> None:
        address_filter = dict(
            is_read_only=False,
            with_utxo=True,
            is_tx_input=True)

        self._utxo_list = list(chain.from_iterable(
            a.utxoList
            for a in self._coin.filterAddressList(**address_filter)))

        self._utxo_amount = sum(u.amount for u in self._utxo_list)

        self.__logUtxoList(
            "Available UTXO's",
            self._utxo_list,
            self._utxo_amount)
        self._selectUtxoList()

    def __logUtxoList(
            self,
            title: str,
            utxo_list: Sequence[Coin.Tx.Utxo],
            utxo_amount: int) -> None:
        if not self._logger.isEnabledFor(logging.DEBUG):
            return
        s = "".join("\n\t" + str(u) for u in utxo_list)
        self._logger.debug(
            "%s:%s\n\ttotal amount: %i",
            title,
            s if s else "\n\tNone",
            utxo_amount)
