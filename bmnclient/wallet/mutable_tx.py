from __future__ import annotations

from typing import TYPE_CHECKING

from ..coins.abstract.mutable_tx import _AbstractMutableTx

if TYPE_CHECKING:
    from ..coins.abstract.coin import AbstractCoin


class MutableTransaction(_AbstractMutableTx):
    def __init__(self, coin: AbstractCoin):
        super().__init__(coin)
        self.__raw__mtx = None
        self.refreshSourceList()

    def filter_sources(self) -> None:
        self._selected_utxo_list, self._selected_utxo_amount = \
            self.select_sources(
                sum((a.utxoList for a in self._source_list), []),
                self._amount + (0 if self._subtract_fee else self.feeAmount),
                getter=lambda a: a.amount)

    @property
    def tx_size(self):
        if not self._source_list:
            return 1024
        return self.estimate_tx_size(
            150,
            max(1, len(self._selected_utxo_list)),
            70,
            2 if self._selected_utxo_amount > self._amount else 1,
        )

    def estimate_tx_size(
            self,
            in_size: int,
            n_in: int,
            out_size: int,
            n_out: int) -> int:
        return (
                in_size
                + len(self._coin.Script.integerToAutoBytes(n_in))
                + out_size
                + len(self._coin.Script.integerToAutoBytes(n_out))
                + 8
        )

    def estimate_confirm_time(self) -> int:
        spb = self._fee_amount_per_byte
        # https://bitcoinfees.net
        if self._receiver_address.type.value.isSegwit:
            spb *= 0.6  # ??
        if spb < 1:
            return -1
        minutes = self._fee_manager.get_minutes(spb)
        return minutes
