# JOK+++
from __future__ import annotations

from typing import TYPE_CHECKING

from ..logger import Logger

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
        self._source_list: List[AbstractAddress] = []
        self._source_amount = 0
        self._amount = 0
        self._subtract_fee = False

        self._model: Optional[MutableTxModelInterface] = \
            self._coin.model_factory(self)

    @property
    def model(self) -> Optional[MutableTxModelInterface]:
        return self._model

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
                self.change)

    @property
    def maxAmount(self) -> int:
        amount = self._source_amount - (0 if self._subtract_fee else self.fee)
        return max(amount, 0)

    @property
    def isValidAmount(self) -> bool:
        if 0 <= self._amount <= self.maxAmount and self.change >= 0:
            return True
        return False
