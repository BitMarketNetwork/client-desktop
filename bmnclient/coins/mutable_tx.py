# JOK+++
from __future__ import annotations

from typing import TYPE_CHECKING

from ..logger import Logger
from ..wallet.fee_manager import FeeManager

if TYPE_CHECKING:
    from typing import List, Optional
    from .address import AbstractAddress
    from .coin import AbstractCoin


class MutableTxModelInterface:
    pass


class AbstractMutableTx:
    def __init__(self, coin: AbstractCoin) -> None:
        self._logger = Logger.getClassLogger(
            __name__,
            self.__class__,
            coin.shortName)
        self._coin = coin
        self._receiver_address: Optional[AbstractCoin._Address] = None
        self._change_address: Optional[AbstractCoin._Address] = None
        self._source_list: List[AbstractAddress] = []
        self._source_amount = 0
        self._amount = 0

        self._subtract_fee = False
        self._fee_manager = FeeManager()  # TODO
        self._fee_amount_per_byte = self._fee_manager.max_spb

        self._selected_utxo_list: List[AbstractCoin.Utxo] = []
        self._selected_utxo_amount = 0

        self.__mtx = None  # TODO tmp

        self._model: Optional[MutableTxModelInterface] = \
            self._coin.model_factory(self)

    @property
    def model(self) -> Optional[MutableTxModelInterface]:
        return self._model

    @property
    def coin(self) -> AbstractCoin:
        return self._coin

    def setReceiverAddressName(self, name: str) -> bool:
        self._receiver_address = self._coin.decodeAddress(name=name)
        if self._receiver_address is None:
            self._logger.warning(
                "Receiver address \"%s\" is invalid.",
                name)
            return False
        else:
            self._logger.debug(
                "Receiver address: %s",
                self._receiver_address.name)
            return True

    @property
    def receiverAddress(self) -> Optional[AbstractCoin._Address]:
        return self._receiver_address

    @property
    def changeAddress(self) -> Optional[AbstractCoin._Address]:
        return self._change_address

    def refreshSourceList(self) -> None:
        self._source_list.clear()
        self._source_amount = 0

        for address in self._coin.addressList:
            if address.readOnly:
                continue

            append = False
            for utxo in address.utxoList:
                if utxo.amount > 0:
                    append = True
                    self._source_amount += utxo.amount

            if append:
                self._source_list.append(address)
                self._logger.debug(
                    "Address \"%s\" appended to source list.",
                    address.name)

        # TODO check,filter unique

        self.filter_sources()

    @property
    def sourceAmount(self) -> int:
        return self._source_amount

    @property
    def amount(self) -> int:
        return self._amount

    @amount.setter
    def amount(self, value: int) -> None:
        if self._amount != value:
            self._amount = value
            self.filter_sources()

            self._logger.debug(
                "Amount: %i, available: %i, change %i",
                value,
                self._source_amount,
                self.changeAmount)

    @property
    def maxAmount(self) -> int:
        amount = self._source_amount
        if not self._subtract_fee:
            amount -= self.feeAmount
        return max(amount, 0)

    @property
    def isValidAmount(self) -> bool:
        if 0 <= self._amount <= self.maxAmount and self.changeAmount >= 0:
            return True
        return False

    @property
    def subtractFee(self) -> bool:
        return self._subtract_fee

    @subtractFee.setter
    def subtractFee(self, value: bool) -> None:
        if self._subtract_fee != value:
            self._subtract_fee = value
            self.filter_sources()

    @property
    def feeAmountPerByteDefault(self) -> int:
        return self._fee_manager.max_spb

    @property
    def feeAmountPerByte(self) -> int:
        return self._fee_amount_per_byte

    @feeAmountPerByte.setter
    def feeAmountPerByte(self, value: int) -> None:
        if self._fee_amount_per_byte != value:
            self._fee_amount_per_byte = value
            self.filter_sources()

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
        if self._subtract_fee and fee_amount > self._amount:
            return False
        return self.changeAmount >= 0

    @property
    def changeAmount(self) -> int:
        change_amount = self._selected_utxo_amount - self._amount
        if not self._subtract_fee:
            change_amount -= self.feeAmount
        return change_amount
