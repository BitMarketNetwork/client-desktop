
import logging
from typing import Optional, Union, List, Tuple

from .. import gcd
from . import coin_network, key, mtx_impl

log = logging.getLogger(__name__)


class NewTxerror(Exception):
    pass


class WrongReceiver(NewTxerror):
    pass


class MutableTransaction:
    """
    wrapper around Mtx
    """
    MAX_SPB_FEE = 200
    MIN_SPB_FEE = 1
    MAX_TX_SIZE = 1024

    def __init__(self, address: str, fee_man: "feeManager", parent=None):
        log.debug(f"New MTX:{address}")
        assert address is not None
        # we need to emit bx result
        self._parent = parent
        # it s serialized MTX!!!s
        self._raw_mtx = None
        self._mtx = None
        self._address = address
        self._receiver: str = ""
        self._receiver_valid: bool = False
        # user fee
        self._outputs = []
        self._amount = None
        self.new_address_for_change = True
        self._leftover_address = None
        self._substract_fee = False

        # ALL source address ( may be filtered by user )
        self._selected_sources = []
        # filtered BY APP source addresses
        self._filtered_addresses = []
        self._filtered_amount = 0
        #
        # self._source_amount =  0

        # strict order !!
        self._fee_man = fee_man
        self._spb = self._fee_man.max_spb
        # setter !
        self._amount = 0
        self.use_coin_balance = True
        self.recalc_sources()
        self.guess_amount()

    @classmethod
    def make_dummy(cls, address: str, parent) -> 'MutableTransaction':
        out = cls(address, gcd.GCD.get_instance().fee_man)
        # third
        out._receiver = 'tb1qs5cz8f0f0l6tf87ez90ageyfm4a7w7rhryzdl2'
        out._amount = 0.01
        out.prepare()
        return out

    def guess_amount(self):
        self.amount = max(self._address.balance -
                          (0 if self._substract_fee else self.fee), 0)

    def recalc_sources(self):
        # TODO: use only one source for a while!!!
        if self._use_coin_balance:
            self._sources = [
                add for add in self._address.coin if add.balance > 0]
        else:
            self._sources = [self._address]
        # addr for addr in self._address.coin.wallets if not addr.readOnly]
        self._selected_sources = [
            add for add in self._sources if add.useAsSource]
        # TODO: get amount from unspents !!!
        self._source_amount = sum(
            add.balance for add in self._selected_sources)
        self.filter_sources()
        if self._amount:
            log.debug(
                f"selected sources {len(self._filtered_addresses)} with total amount in {self._source_amount}. Change is {self.change}")

    @classmethod
    def _filter_addresses(cls, sources: list, target_amount) -> Tuple[list, int]:
        """
        make it static to be clear
        it is simple for a while.. but it's supposed to be more smart
        """
        sorted_list = sorted(sources, key=lambda a: a.balance)
        result_list = []
        amount = 0
        for src in sorted_list:
            amount += src.balance
            result_list.append(src)
            if amount >= target_amount:
                return result_list, amount
        return sources , target_amount

    def filter_sources(self) -> None:
        self._filtered_addresses, self._filtered_amount = self._filter_addresses(
            self._selected_sources, self._amount -
            (0 if self._substract_fee else self.fee)
        )

    def prepare(self):
        """
        raise stricly before any changes !!!
        """
        self._test_receiver()
        #
        if 0 == self.fee:
            raise NewTxerror(f"No fee")
        if self._substract_fee and self.fee > self._amount:
            raise NewTxerror(
                f"Fee {self.fee} more than amount {self._amount}")
        if not self._filtered_addresses:
            raise NewTxerror(f"There are no source addresses selected")
        if self._amount > self._filtered_amount:
            raise NewTxerror(
                f"Amount {self._amount} more than balance {self._filtered_amount}")
        # filter sources. some smart algo expected here
        # prepare
        sources: List[Tuple[List[mtx_impl.UTXO, key.PrivateKey]]] = [
            (ad.unspents, ad.private_key) for ad in self._filtered_addresses]
        _unspents = sum((un for un, _ in sources), [])
        _unspent_sum = sum( (u.amount for u in _unspents ))
        log.debug(f"unspents: {_unspents} sum: {_unspent_sum} vs {self._filtered_amount}")
        if not sources:
            raise NewTxerror(f"No unspent outputs found")
        # process fee
        if self._substract_fee:
            _outputs = [
                (self._receiver, int(self._amount - self.fee))
            ]
        else:
            _outputs = [
                (self._receiver, int(self._amount)),
            ]

        log.debug(
            f"amount:{self._amount} fee:{self.fee} fact_change:{self.change}")
        # process leftover
        if self.change > 0:
            if self.new_address_for_change:
                self._leftover_address = self._address.coin.make_address()
            else:
                self._leftover_address = self._address

            _outputs.append(
                (self._leftover_address.name, self.change)
            )
        else:
            self._leftover_address = None

        log.debug(
            f"outputs: {_outputs} change_wallet:{self._leftover_address}")

        self._mtx = mtx_impl.Mtx.make(
            _unspents,
            _outputs,
        )
        log.debug(f"TX fee: {self._mtx.fee}")
        if self._mtx.fee != self.fee:
            self.cancel()
            log.error(
                f"Fee error. Should be {self.fee} but has {self._mtx.fee}")
            raise NewTxerror("Critical error. Fee mismatch")
        for utxo, key_ in sources:
            self._mtx.sign(key_, unspents=utxo)
        self._raw_mtx = self._mtx.to_hex()
        log.info(f"final TX to send: {self._mtx}")

    @property
    def change(self):
        # TODO:
        ch = int(self._filtered_amount - self._amount -
                 (0 if self._substract_fee else self.fee))
        log.debug( f"source:{self._filtered_amount} am:{self._amount} \
        # fee:{self.fee} substract: {self.substract_fee}: change: {ch}")
        return ch

    def cancel(self):
        if self._leftover_address:
            self._leftover_address.coin.remove_wallet(self._leftover_address)
            self._leftover_address = None

    def send(self):
        gcd.GCD.get_instance().broadcastMtx.emit(self)

    def send_callback(self, ok: bool, error: Optional[str] = None):
        # not GUI thread !!!
        log.debug(f"send result:{ok} error:{error}")
        if self._parent:
            if ok:
                self._parent.sent.emit()
                # add locally and check mempool
                tx_ = self._mtx.to_tx()
                tx_.fromAddress = self._address.name
                tx_.toAddress = self._receiver
                self._address.insert_new(tx_)

                gcd.GCD.get_instance().mempoolCoin.emit(self._address.coin)

                # check for sender
                # TODO: not addres !!! all filtered_src
                # gcd.GCD.get_instance().mempoolAddress.emit(self._address)
                # # check for change
                # if self._leftover_address:
                #     gcd.GCD.get_instance().mempoolAddress.emit(self._leftover_address)
                # # check for receiver
                # receiver = self._address.coin[self._receiver]
                # if receiver:
                #     gcd.GCD.get_instance().mempoolAddress.emit(receiver)
            else:
                self._parent.fail.emit(str(error))

    @property
    def tx_size(self):
        if not self._selected_sources:
            return self.MAX_TX_SIZE
        return mtx_impl.estimate_tx_size(
            150,
            max(1, len(self._filtered_addresses)),
            70,
            2 if self._filtered_amount > self._amount else 1,
        )

    def estimate_confirm_time(self) -> int:
        spb = self._spb
        # https://bitcoinfees.net
        if key.AddressString.is_segwit(self._receiver):
            spb *= 0.6  # ??
        if spb < self.MIN_SPB_FEE:
            return -1
        minutes = self._fee_man.get_minutes(spb)
        return minutes

    def _test_receiver(self) -> None:
        self._receiver_valid = False
        if not self._receiver:
            raise WrongReceiver("No receiver")
        if not key.AddressString.validate_bool(self._receiver):
            raise WrongReceiver("Invalid receiver address")
        target_net = coin_network.CoinNetworkBase.from_address(self._receiver)
        if target_net:
            if target_net != self._address.coin.NETWORK:
                raise WrongReceiver("Wrong network")
        self._receiver_valid = True

    @property
    def receiver(self):
        return self._receiver

    @property
    def receiver_valid(self):
        return self._receiver_valid

    @receiver.setter
    def receiver(self, addr: str):
        self._receiver = addr
        try:
            self._test_receiver()
        except WrongReceiver as err:
            log.warning(f"{addr} => {err}")
            self._receiver = ""

    @property
    def source_amount(self) -> int:
        return self._source_amount

    @property
    def use_coin_balance(self) -> bool:
        return self._use_coin_balance

    @use_coin_balance.setter
    def use_coin_balance(self, value: bool) -> None:
        self._use_coin_balance = value
        self.recalc_sources()

    @property
    def address(self) -> "CAddress":
        return self._address

    @property
    def leftover_address(self):
        log.warning(self._leftover_address)
        if self._leftover_address:
            return self._leftover_address.name
        return ""

    @property
    def amount(self):
        return int(self._amount)

    @amount.setter
    def amount(self, val):
        self._amount = val
        self.filter_sources()
        log.info(f"amount: {self._amount} change:{self.change}")

    @property
    def tx_id(self):
        if self._mtx:
            return self._mtx.id

    @property
    def fee(self) -> int:
        return int(self._spb * self.tx_size)

    @property
    def sources(self):
        return self._sources

    @property
    def coin(self):
        return self._address.coin

    @property
    def substract_fee(self) -> bool:
        return self._substract_fee

    @substract_fee.setter
    def substract_fee(self, value: bool) -> None:
        self._substract_fee = value
        self.filter_sources()

    @property
    def spb(self) -> int:
        return int(self._spb)

    @spb.setter
    def spb(self, value):
        log.debug(f"SPB: {value}")
        self._spb = value
        self.filter_sources()

    def __str__(self) -> str:
        return self._raw_mtx
