import collections
import functools
import itertools
import logging
from typing import DefaultDict, List, Optional, Tuple

from . import key, mtx_impl
from .coins import CoinType

log = logging.getLogger(__name__)


def perms(src: list, getter: callable):
    for i in range(len(src)):
        for pack in itertools.combinations(src, r=i + 1):
            yield pack, sum(map(getter, pack))


class NewTxerror(Exception):
    pass


class MutableTransaction:
    MAX_SPB_FEE = 200
    MIN_SPB_FEE = 1
    MAX_TX_SIZE = 1024

    def __init__(self, coin: CoinType, fee_man: "feeManager", parent=None):
        # we need to emit bx result
        self._coin = coin
        self.__parent = parent
        # it s serialized MTX!!!s
        self.__raw__mtx = None
        self.__mtx = None
        self.__receiver = ""
        self.__amount = None
        self.new_address_for_change = True
        self.__leftover_address = None
        self.__substract_fee = False

        # ALL source address ( may be filtered by user )
        self.__selected_sources: List['address.CAdress'] = []
        # wrong way !!! need to select UNSPENTS not addresses
        self.__filtered_inputs: List[mtx_impl.TxInput] = []
        self.__filtered_amount = 0

        # strict order !!
        self.__fee_man = fee_man
        self._spb = self.__fee_man.max_spb
        # setter !
        self.__amount = 0
        self.recalc_sources()
        self.set_max()

    def recalc_sources(self, auto: bool = False):
        if auto:
            for add in self.__sources:
                add.useAsSource = True
        self.__sources = [add for add in self._coin.addressList if add.amount > 0]

        log.warning(f"{self.__sources }")
        # addr for addr in self.__address.coin.addressList if not addr.readOnly]
        self.__selected_sources: List['address.CAddress'] = self.__sources if auto else [
            add for add in self.__sources if add.useAsSource]
        self.__source_amount = sum(
            add.amount for add in self.__selected_sources)
        self.filter_sources()
        log.debug(
            f"source addresses:{len(self.__selected_sources)} ({self.__source_amount}) selected inputs {len(self.__filtered_inputs)} ({self.__filtered_amount}). Change is {self.change}")

    @classmethod
    def select_sources(cls, sources: list, target_amount: int, getter: callable) -> Tuple[list, int]:

        if not sources or target_amount <= 0:
            return [], 0

        def src_len_select(src):
            return max(src, key=lambda s: len(s[0]))

        # try simple cases
        summ = sum(map(getter, sources))
        # log.warning(f"sum:{summ} t:{target_amount}")
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
        all_inputs = sum((a.unspents for a in self.__selected_sources), [])
        target = self.__amount + (0 if self.__substract_fee else self.fee)
        self.__filtered_inputs, self.__filtered_amount = self.select_sources(
            all_inputs, target,
            getter=lambda a: a.amount
        )
        # log.warning(
        #     f"amount:{self.__amount} .  filter=>{[[u.amount for u in a.unspents] for a in self.__selected_sources]} target:{target} result:{self.__filtered_amount}")

        # ensure uniqueness
        # assert len(set(self.__filtered_inputs)) == len(
        #     self.__filtered_inputs)

    def prepare(self):
        if 0 == self.fee:
            raise NewTxerror(f"No fee")
        if self.__substract_fee and self.fee > self.__amount:
            raise NewTxerror(
                f"Fee {self.fee} more than amount {self.__amount}")
        if not self.__filtered_inputs:
            raise NewTxerror(f"There are no source inputs selected")
        if self.__amount > self.__filtered_amount:
            raise NewTxerror(
                f"Amount {self.__amount} more than balance {self.__filtered_amount}")
        # filter sources. some smart algo expected here
        # prepare
        unspents = self.__filtered_inputs
        unspent_sum = sum(u.amount for u in unspents)

        def cl(t, i):
            t[i.address] += [i]
            return t
        sources: DefaultDict['address.CAddress',
                             List[mtx_impl.UTXO]] = functools.reduce(
                                 cl,
                                 unspents,
            collections.defaultdict(list),
        )
        log.debug(
            f"unspents: {unspents} scr:{sources} sum: {unspent_sum} vs {self.__filtered_amount}")
        if not sources:
            raise NewTxerror(f"No unspent outputs found")
        # process fee
        if self.__substract_fee:
            outputs = [
                (self.__receiver, int(self.__amount - self.fee))
            ]
        else:
            outputs = [
                (self.__receiver, int(self.__amount)),
            ]

        log.debug(
            f"amount:{self.__amount} fee:{self.fee} fact_change:{self.change}")
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

        log.debug(
            f"outputs: {outputs} change_wallet:{self.__leftover_address}")

        self.__mtx = mtx_impl.Mtx.make(
            unspents,
            outputs,
        )
        log.debug(f"TX fee: {self.__mtx.fee}")
        if self.__mtx.fee != self.fee:
            #self.cancel()
            log.error(
                f"Fee failure. Should be {self.fee} but has {self.__mtx.fee}")
            raise NewTxerror("Critical error. Fee mismatch")
        for addr, utxo in sources.items():
            log.debug(f"INPUT: address:{addr.name} utxo:{len(utxo)}")
            self.__mtx.sign(addr.private_key, unspents=utxo)
        self.__raw__mtx = self.__mtx.to_hex()
        log.info(f"final TX to send: {self.__mtx}")

    def send(self):
        from ..application import CoreApplication
        CoreApplication.instance().networkThread.broadcastMtx.emit(self)

    def send_callback(self, ok: bool, error: Optional[str] = None):
        log.debug(f"send result:{ok} error:{error}")
        if ok:
            from ..application import CoreApplication
            CoreApplication.instance().networkThread.mempoolCoin.emit(self._coin)
        else:
            if self.__parent:
                self.__parent.fail.emit(str(error))

    @ property
    def tx_size(self):
        if not self.__selected_sources:
            return self.MAX_TX_SIZE
        return mtx_impl.estimate_tx_size(
            150,
            max(1, len(self.__filtered_inputs)),
            70,
            2 if self.__filtered_amount > self.__amount else 1,
        )

    def estimate_confirm_time(self) -> int:
        spb = self._spb
        # https://bitcoinfees.net
        if key.AddressString.is_segwit(self.__receiver):
            spb *= 0.6  # ??
        if spb < self.MIN_SPB_FEE:
            return -1
        minutes = self.__fee_man.get_minutes(spb)
        return minutes

    @ property
    def receiver(self) -> str:
        return self.__receiver

    @ property
    def receiver_valid(self) -> bool:
        return self.coin.decodeAddress(name=self.__receiver) is not None

    def setReceiverAddressName(self, name: str):
        if self.coin.decodeAddress(name=name) is None:
            self.__receiver = ""
            return False
        self.__receiver = name
        return True

    @ property
    def source_amount(self) -> int:
        return self.__source_amount

    @ property
    def filtered_amount(self) -> int:
        return self.__filtered_amount

    @ property
    def leftover_address(self):
        if self.__leftover_address:
            return self.__leftover_address.name
        return ""

    def get_max_amount(self) -> int:
        return max(self.__source_amount - (0 if self.__substract_fee else self.fee), 0)

    def set_max(self) -> None:
        self.amount = self.get_max_amount()

    @ property
    def amount(self):
        return int(self.__amount)

    @ amount.setter
    def amount(self, value: int) -> None:
        self.__amount = value
        self.filter_sources()
        log.info(
            f"amount: {value} available:{self.__source_amount} change:{self.change}")

    @ property
    def change(self):
        # res = int(self.__filtered_amount - self.__amount - (0 if self.__substract_fee else self.fee))
        # log.info(f"source:{self.__filtered_amount} am:{self.__amount} \
        #     fee:{self.fee} substract: {self.subtract_fee}: change:{res}")

        return int(self.__filtered_amount - self.__amount - (0 if self.__substract_fee else self.fee))

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
        return self.__sources

    @ property
    def coin(self):
        return self._coin

    @ property
    def subtract_fee(self) -> bool:
        return self.__substract_fee

    @ subtract_fee.setter
    def subtract_fee(self, value: bool) -> None:
        self.__substract_fee = value
        self.filter_sources()

    def spb_default(self):
        return self.__fee_man.max_spb

    @ property
    def spb(self) -> int:
        return int(self._spb)

    @ spb.setter
    def spb(self, value):
        log.debug(f"SPB: {value}")
        self._spb = value
        self.filter_sources()

    def __str__(self) -> str:
        return self.__raw__mtx
