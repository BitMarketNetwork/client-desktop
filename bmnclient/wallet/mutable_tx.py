from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

from . import key, mtx_impl
from ..coins.mutable_tx import AbstractMutableTx

if TYPE_CHECKING:
    from typing import Tuple
    from ..coins.coin import AbstractCoin


class MutableTransaction(AbstractMutableTx):
    MAX_SPB_FEE = 200
    MIN_SPB_FEE = 1
    MAX_TX_SIZE = 1024

    def __init__(self, coin: AbstractCoin):
        super().__init__(coin)
        self.__raw__mtx = None
        self.refreshSourceList()

    @classmethod
    def perms(cls, src: list, getter: callable):
        for i in range(len(src)):
            for pack in itertools.combinations(src, r=i + 1):
                yield pack, sum(map(getter, pack))

    @classmethod
    def select_sources(
            cls,
            source_list: list,
            target_amount: int,
            getter: callable) -> Tuple[list, int]:
        if not source_list or target_amount <= 0:
            return [], 0

        def src_len_select(src):
            return max(src, key=lambda s: len(s[0]))

        # try simple cases
        summ = sum(map(getter, source_list))
        # self._logger.warning(f"sum:{summ} t:{target_amount}")
        if summ < target_amount:
            return [], summ
        if summ == target_amount:
            return source_list, target_amount

        # try exact products
        res = ((s, c) for s, c in cls.perms(source_list, getter) if c == target_amount)
        # there's no way to test generator
        try:
            return src_len_select(res)
        except ValueError:
            pass

        res = [(s, c) for s, c in cls.perms(source_list, getter) if c > target_amount]
        # two loops :-\
        if res:
            _, min_ = min(res, key=lambda r: r[1])
            return src_len_select(r for r in res if r[1] == min_)

        # # fallback to the silliest algo
        sorted_list = sorted(source_list, key=getter, reverse=True)
        result_list = []
        amount = 0
        prev = None
        for src in sorted_list:
            if getter(src) > target_amount:
                prev = src
                continue
            if prev and getter(src) < target_amount:
                src = prev
            amount += getter(src)
            result_list.append(src)
            if amount >= target_amount:
                return result_list, amount
        return [], 0

    def filter_sources(self) -> None:
        self._selected_utxo_list, self._selected_utxo_amount = \
            self.select_sources(
                sum((a.utxoList for a in self._source_list), []),
                self._amount + (0 if self._subtract_fee else self.feeAmount),
                getter=lambda a: a.amount)

    @ property
    def tx_size(self):
        if not self._source_list:
            return self.MAX_TX_SIZE
        return mtx_impl.estimate_tx_size(
            150,
            max(1, len(self._selected_utxo_list)),
            70,
            2 if self._selected_utxo_amount > self._amount else 1,
        )

    def estimate_confirm_time(self) -> int:
        spb = self._fee_amount_per_byte
        # https://bitcoinfees.net
        if key.AddressString.is_segwit(self._receiver_address.name):
            spb *= 0.6  # ??
        if spb < self.MIN_SPB_FEE:
            return -1
        minutes = self._fee_manager.get_minutes(spb)
        return minutes
