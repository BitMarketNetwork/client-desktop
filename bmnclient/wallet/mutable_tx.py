from __future__ import annotations

import collections
import functools
import itertools
from typing import TYPE_CHECKING

from . import key, mtx_impl
from ..coins.mutable_tx import AbstractMutableTx

if TYPE_CHECKING:
    from typing import DefaultDict, List, Optional, Tuple
    from ..coins.coin import AbstractCoin


def perms(src: list, getter: callable):
    for i in range(len(src)):
        for pack in itertools.combinations(src, r=i + 1):
            yield pack, sum(map(getter, pack))


class NewTxerror(Exception):
    pass


class MutableTransaction(AbstractMutableTx):
    MAX_SPB_FEE = 200
    MIN_SPB_FEE = 1
    MAX_TX_SIZE = 1024

    def __init__(self, coin: AbstractCoin):
        super().__init__(coin)

        # it s serialized MTX!!!s
        self.__raw__mtx = None
        self.__mtx = None
        self.new_address_for_change = True
        self.__leftover_address = None

        # wrong way !!! need to select UNSPENTS not addresses
        self.__filtered_inputs: List[mtx_impl.TxInput] = []
        self.__filtered_amount = 0

        # setter !
        self.refreshSourceList()

    @classmethod
    def select_sources(cls, sources: list, target_amount: int, getter: callable) -> Tuple[list, int]:
        if not sources or target_amount <= 0:
            return [], 0

        def src_len_select(src):
            return max(src, key=lambda s: len(s[0]))

        # try simple cases
        summ = sum(map(getter, sources))
        # self._logger.warning(f"sum:{summ} t:{target_amount}")
        if summ < target_amount:
            return [], summ
        if summ == target_amount:
            return sources, target_amount

        # try exact products
        res = ((s, c)
               for s, c in perms(sources, getter) if c == target_amount)
        # there's no way to test generator
        try:
            return src_len_select(res)
        except ValueError:
            pass

        res = [(s, c) for s, c in perms(sources, getter) if c > target_amount]
        # two loops :-\
        if res:
            _, min_ = min(res, key=lambda r: r[1])
            return src_len_select(r for r in res if r[1] == min_)

        # # fallback to the silliest algo
        sorted_list = sorted(sources, key=getter, reverse=True)
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
        all_inputs = sum((a.utxoList for a in self._source_list), [])
        target = self._amount + (0 if self._subtract_fee else self.fee)

        self.__filtered_inputs, self.__filtered_amount = self.select_sources(
            all_inputs,
            target,
            getter=lambda a: a.amount)

    def prepare(self):
        if 0 == self.fee:
            raise NewTxerror(f"No fee")
        if self._subtract_fee and self.fee > self._amount:
            raise NewTxerror(
                f"Fee {self.fee} more than amount {self._amount}")
        if not self.__filtered_inputs:
            raise NewTxerror(f"There are no source inputs selected")
        if self._amount > self.__filtered_amount:
            raise NewTxerror(
                f"Amount {self._amount} more than balance {self.__filtered_amount}")
        # filter sources. some smart algo expected here
        # prepare
        utxo_list = self.__filtered_inputs
        unspent_sum = sum(u.amount for u in utxo_list)

        def cl(t, i):
            t[i.address] += [i]
            return t
        sources: DefaultDict['address.CAddress', List[mtx_impl.UTXO]] = \
            functools.reduce(cl, utxo_list, collections.defaultdict(list),)
        self._logger.debug(
            f"unspents: {utxo_list} scr:{sources} sum: {unspent_sum} vs {self.__filtered_amount}")
        if not sources:
            raise NewTxerror(f"No unspent outputs found")
        # process fee
        if self._subtract_fee:
            outputs = [
                (self._receiver_address.name, int(self._amount - self.fee))
            ]
        else:
            outputs = [
                (self._receiver_address.name, int(self._amount)),
            ]

        self._logger.debug(
            f"amount:{self._amount} fee:{self.fee} fact_change:{self.change}")
        # process leftover
        if self.change > 0:
            if self.new_address_for_change:
                self.__leftover_address = self._coin.make_address()
            else:
                self.__leftover_address = self._coin.make_address()

            outputs.append(
                (self.__leftover_address.name, self.change)
            )
        else:
            self.__leftover_address = None

        self._logger.debug(
            f"outputs: {outputs} change_wallet:{self.__leftover_address}")

        self.__mtx = mtx_impl.Mtx.make(utxo_list, outputs)
        self._logger.debug(f"TX fee: {self.__mtx.fee}")
        if self.__mtx.fee != self.fee:
            #self.cancel()
            self._logger.error(
                f"Fee failure. Should be {self.fee} but has {self.__mtx.fee}")
            raise NewTxerror("Critical error. Fee mismatch")
        for addr, utxo in sources.items():
            self._logger.debug(f"INPUT: address:{addr.name} utxo:{len(utxo)}")
            self.__mtx.sign(addr.private_key, utxo_list=utxo)
        self.__raw__mtx = self.__mtx.to_hex()
        self._logger.info(f"final TX to send: {self.__mtx}")

    def send(self):
        from ..application import CoreApplication
        CoreApplication.instance().networkThread.broadcastMtx.emit(self)

    def send_callback(self, ok: bool, error: Optional[str] = None):
        self._logger.debug(f"send result:{ok} error:{error}")
        if ok:
            pass
            # AddressMultyMempoolCommand(coin.addressList, self))
        else:
            if self.__parent:
                self.__parent.fail.emit(str(error))

    @ property
    def tx_size(self):
        if not self._source_list:
            return self.MAX_TX_SIZE
        return mtx_impl.estimate_tx_size(
            150,
            max(1, len(self.__filtered_inputs)),
            70,
            2 if self.__filtered_amount > self._amount else 1,
        )

    def estimate_confirm_time(self) -> int:
        spb = self._spb
        # https://bitcoinfees.net
        if key.AddressString.is_segwit(self._receiver_address.name):
            spb *= 0.6  # ??
        if spb < self.MIN_SPB_FEE:
            return -1
        minutes = self.__fee_man.get_minutes(spb)
        return minutes

    @ property
    def filtered_amount(self) -> int:
        return self.__filtered_amount

    @ property
    def leftover_address(self):
        if self.__leftover_address:
            return self.__leftover_address.name
        return ""

    @ property
    def change(self):
        # res = int(self.__filtered_amount - self._amount - (0 if self._subtract_fee else self.fee))
        # self._logger.info(f"source:{self.__filtered_amount} am:{self._amount} \
        #     fee:{self.fee} substract: {self.subtract_fee}: change:{res}")

        return int(self.__filtered_amount - self._amount - (0 if self._subtract_fee else self.fee))

    @ property
    def tx_id(self):
        if self.__mtx:
            return self.__mtx.id

    # for tests
    @ property
    def mtx(self):
        return self.__mtx

    @ property
    def fee(self) -> int:
        return int(self._spb * self.tx_size)

    def fee_default(self):
        return int(self.__fee_man.max_spb * self.tx_size)

    @fee.setter
    def fee(self, value: int):
        self._spb = value // self.tx_size

    @ property
    def sources(self):
        return self._source_list

    @ property
    def coin(self):
        return self._coin

    @ property
    def subtract_fee(self) -> bool:
        return self._subtract_fee

    @ subtract_fee.setter
    def subtract_fee(self, value: bool) -> None:
        self._subtract_fee = value
        self.filter_sources()

    def spb_default(self):
        return self.__fee_man.max_spb

    @ property
    def spb(self) -> int:
        return int(self._spb)

    @ spb.setter
    def spb(self, value):
        self._logger.debug(f"SPB: {value}")
        self._spb = value
        self.filter_sources()
