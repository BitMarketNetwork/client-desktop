import logging
from functools import partial
import itertools
from typing import Iterable, List, Optional, Union

import PySide2.QtCore as qt_core

from .. import meta, orderedset
# linter
from . import (abs_coin, address, root_address, address_model, coin_network, hd, key,
               serialization)

log = logging.getLogger(__name__)

ADDRESS_NAMES = "__address_names"


# locale.setlocale(locale.LC_ALL, 'en_US.utf8')


class SelectAddressError(Exception):
    pass


def network_tag(net: coin_network.CoinNetworkBase) -> str:
    return next(c.name for c in CoinType.all if c.network == net)  # pylint: disable=E1133


class CoinType(abs_coin.CoinBase, serialization.SerializeMixin):
    # decimal points
    _default_fee = 10000
    # [[https://github.com/satoshilabs/slips/blob/master/slip-0044.md|SLIP-0044 : Registered coin types for BIP-0044]]
    _hd_index: int = None
    network: coin_network.CoinNetworkBase = None
    # testnet ID is the same for all coins
    TEST_HD_INDEX = 1
    #
    statusChanged = qt_core.Signal()
    heightChanged = qt_core.Signal()
    balanceChanged = qt_core.Signal()
    expandedChanged = qt_core.Signal()
    visibleChanged = qt_core.Signal()
    invalidServer = qt_core.Signal()
    addAddress = qt_core.Signal(address.CAddress)

    @meta.classproperty
    def all(cls) -> Iterable:  # pylint: disable=E0213
        return (val for _, val in globals().items() if isinstance(val, type) and issubclass(val, cls) and val is not cls)

    def __init__(self, parent):
        super().__init__(parent=parent)
        self._set_object_name(self.name)
        self.__height = None
        self.__offset = None
        #
        self.__verified_height = None
        self.__unverified_offset = None
        self.__unverified_hash = None
        #
        self.__status = None
        self.__wallet_list = []
        address_model_ = address_model.AddressModel(self)
        self.__address_model = address_model.AddressProxyModel(self)
        self.__address_model.setSourceModel(address_model_)
        self.__current_wallet = 0
        self.__hd_node = None
        self.__expanded = False
        self.__visible = True
        self.__tx_set = orderedset.OrderedSet()
        self.root = root_address.RootAddress(self)
        self.addAddress.connect(self.addAddressImpl,
                                qt_core.Qt.QueuedConnection)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        #if not e_logger.SILENCE_VERBOSITY and cls._enabled:
        #    print(f"coin => {cls.__name__}")

    def __str__(self) -> str:
        return f"<{self.full_name},{self.rowid} vis:{self.__visible}>"

    def hd_address(self, hd_index: int) -> str:
        if self.__hd_node is None:
            raise address.AddressError(f"There's no private key in {self}")
        return self.__hd_node.make_child_prv(
            hd_index,
            False,
            self.network)

    def reset_cell(self):
        self.__address_model.reset()

    @qt_core.Slot(address.CAddress)
    def addAddressImpl(self, wallet: address.CAddress) -> None:
        assert qt_core.QThread.currentThread() == self.thread()
        self.__address_model.append()
        self.__wallet_list.append(wallet)
        self.update_balance()
        self.__address_model.append_complete()
        self._reset_address_names()

        #
        from ..ui.gui import Application
        Application.instance().coinManager.render_cell(self)
        # self.reset_cell()

        if self.parent():
            self.parent().update_wallet(wallet)
        wallet.updatingChanged.connect(
            partial(self.__address_model.address_updated, wallet), qt_core.Qt.QueuedConnection)
        wallet.balanceChanged.connect(
            partial(self.__address_model.balance_changed, wallet), qt_core.Qt.QueuedConnection)

    def _next_hd_index(self):
        idxs = [a.hd_index for a in self.__wallet_list]
        return next(k for k in itertools.count(1) if k not in idxs)

    def make_address(self, type_: key.AddressType = key.AddressType.P2WPKH, label: str = "", message: str = "") -> address.CAddress:
        """
        create NEW active address ( with keys)
        """
        if self.__hd_node is None:
            raise address.AddressError(f"There's no private key in {self}")
        hd_index = 1
        while any(w.hd_index == hd_index for w in self.__wallet_list):
            hd_index += 1
        new_hd = self.__hd_node.make_child_prv(
            self._next_hd_index(),
            False,
            self.network)
        wallet = address.CAddress.make_from_hd(new_hd, self, type_)
        assert wallet.hd_index == hd_index
        wallet.label = label
        wallet._message = message
        # log.debug(
        #     f"New wallet {wallet}  created from HD: {new_hd.chain_path} net:{self.network}")
        if self.parent():
            self.parent().save_wallet(wallet)
            self.addAddress.emit(wallet)
        else:
            self.addAddressImpl(wallet)
        return wallet

    def add_watch_address(self, name: str, label: str = "") -> address.CAddress:
        # self(name)
        adr = address.CAddress(name, self, created=True)
        adr.create()
        adr.label = label
        if self.parent():
            self.addAddress.emit(adr)
            self.parent().save_wallet(adr)
        else:
            # for tests
            self.addAddressImpl(adr)
        return adr

    def append_address(self, name: str, *args) -> address.CAddress:
        assert isinstance(name, str), f"name is {type(name)}: {name}"
        """
        make address structure from data.
        """
        has = [n for n in self.__wallet_list if name.strip().casefold() ==
               n.name.casefold()]
        if has:
            log.warn(f"Address {name} already exists")
            return has[0]
        #
        if qt_core.QThread.currentThread() != self.thread():
            w = address.CAddress(name)
            w.moveToThread(self.thread())
            w.setParent(self)
            # USE SETTER !!! pay attention to connections
            w.coin = self
        else:
            w = address.CAddress(name, self)
        w.create()
        if args:
            try:
                w.from_args(iter(args))
            except TypeError as terr:
                log.warning(
                    f"bad arguments: {args} for loading address:{terr}")
        self.addAddress.emit(w)

        return w

    def to_table(self) -> dict:
        return {
            "name": self.name,
            "visible": self.__visible,
            "addresses": [w.to_table() for w in self.__wallet_list],
        }

    def from_table(self, table: dict):
        assert self.name == table["name"]
        self.visible = table["visible"]
        self.__wallet_list.clear()
        for addr_t in table["addresses"]:
            wallet = address.CAddress.from_table(addr_t, self)
            self.__wallet_list.append(wallet)
        self._reset_address_names()

    @classmethod
    def match(cls, name: str) -> bool:
        "Match coin by string input"
        name_ = name.strip().casefold()
        return name_ in [
            cls.name.casefold(),
            cls.full_name.casefold(),
        ]

    def _validate_address(self, addr: str):
        key.AddressString.validate(addr)

    def update_balance(self):
        self._balance = sum(int(w.balance)
                            for w in self.__wallet_list if not w.readOnly)
        # log.warning(f"BALANCE UPDATED: {self} {self._balance}")
        self.balanceChanged.emit()

    def make_hd_node(self, parent_node):
        self.__hd_node = parent_node.make_child_prv(
            self.TEST_HD_INDEX if self._test else self._hd_index, True, self.network)

    @property
    def hd_node(self) -> hd.HDNode:
        return self.__hd_node

    @property
    def private_key(self) -> key.PrivateKey:
        if self.__hd_node:
            return self.__hd_node.key

    def add_tx(self, tx_: 'tx.Transaction') -> None:
        self.__tx_set.add(tx_, 0)

    def add_tx_list(self, tx_list: Iterable['tx.Transaction']) -> None:
        # TDO: optimize
        for tx_ in tx_list:
            self.__tx_set.add(tx_, 0)

    def update_tx_list(self):
        self.__tx_set.clear()
        for w in self.__wallet_list:
            self.add_tx_list(w.tx_list)

    @property
    def tx_count(self) -> int:
        # return sum(len(w) for w in self.__wallet_list)
        return len(self.__tx_set)

    def get_tx(self, idx: int) -> 'tx.Transaction':
        return self.__tx_set[idx]

    @property
    def server_tx_count(self) -> int:
        return sum(w.txCount for w in self.__wallet_list)

    def empty(self, skip_zero: bool) -> bool:
        if skip_zero:
            return next((w for w in self.__wallet_list if not w.empty_balance), None) is None
        return not self

    def __iter__(self) -> "CoinType":
        self.__wallet_iter = iter(self.__wallet_list)
        return self

    def __next__(self) -> address.CAddress:
        return next(self.__wallet_iter)

    # abc implemented it but we can do it better
    def __contains__(self, value: Union[str, address.CAddress]) -> bool:
        if not isinstance(value, str):
            value = value.name
        return any(value == add.name for add in self.__wallet_list)

    def __len__(self) -> int:
        return len(self.__wallet_list)

    def __bool__(self) -> bool:
        return bool(self.__wallet_list)

    # don't bind not_empty with addressModel !!! . beware recursion
    def __getitem__(self, key: Union[int, str]) -> address.CAddress:
        if isinstance(key, int):
            return self.__wallet_list[key]
        if isinstance(key, str):
            return next((w for w in self.__wallet_list if w.name == key), None)

    def __call__(self, idx: int) -> address.CAddress:
        "Filtered version of getitem"
        return self.__address_model(idx)

    def __update_wallets(self, from_=Optional[int], remove_txs_from: Optional[int] = None, verbose: bool = False):
        "from old to new one !!!"
        for w in self.__wallet_list:
            w.update_tx_list(from_, remove_txs_from, verbose)
        # it must be called when height changed
        # self.gcd.coin_height_changed(self)

    def parse_coin(self, data: dict, poll: bool, **kwargs) -> bool:
        """
        poll - regular polling (not at start)

        next cases here:
        - return true to update coin in db
        - emit height changed to update tx list
        - change coin status
        - mark server as invalid
        """

        verbose = kwargs.get("verbose", False)
        changed = False
        verified_height = int(data["verified_height"])
        unverified_hash = data["unverified_hash"]
        unverified_offset = data["unverified_offset"]
        height = int(data["height"])
        offset = data["offset"]
        status = int(data["status"])

        def update_local_data():
            self.__verified_height = verified_height
            self.__unverified_hash = unverified_hash
            self.__unverified_offset = unverified_offset
            self.__offset = offset
            if verbose and self.__height != height:
                log.warning(f"height changed for {self} to {height}")
            self.height = height

        if status != self.__status:
            self.__status = status
            self.statusChanged.emit()
            if status == 0:
                return True

        # wrong signature => there's no point to see more, total update
        if self.__unverified_hash is None:
            if verbose:
                log.warning(f"NO LOCAL COIN HASH => {self}")

            self.__update_wallets(verbose=verbose)
            update_local_data()

            return True

        # don't clear what to do exactly
        if self.__verified_height and self.__verified_height > verified_height:
            log.error(
                f"server verified height is more than local one. Server is invalid")
            self.invalidServer.emit()
            return False

        #
        if verbose:
            log.warning(f"data {data} uoff:{unverified_offset}")

        if unverified_hash != self.__unverified_hash:
            if verbose:
                log.warning(
                    f"Need to delete local tx data from {self.__verified_height} for {self}. update from {self.__unverified_offset}")
            self.__update_wallets(self.__unverified_offset,
                                  self.__verified_height, verbose=verbose)
            update_local_data()
            return True

        if offset != self.__offset:
            if verbose:
                log.info(
                    f"Coin offset changed to {offset} for {self}. update from {self.__offset}")
            self.__update_wallets(self.__offset, verbose=verbose)
            update_local_data()
            return True

        return False

    def remove_wallet(self, wallet: address.CAddress):
        index = self.__wallet_list.index(wallet)
        # self.__wallet_list.remove(wallet)
        wallet.clear()
        self.__address_model.remove(index)
        del self.__wallet_list[index]
        self.__address_model.remove_complete()
        self.update_balance()
        self._reset_address_names()

    def clear(self):
        for addr in self.__wallet_list:
            addr.clear()
        self.__wallet_list.clear()
        self.update_balance()

    def _set_height(self, hei: int):
        if hei != self.__height:
            self.__height = hei
            self.heightChanged.emit()  # why no ???

    def _get_height(self) -> int:
        return self.__height

    @property
    def gcd(self) -> "GCD":
        return self.parent()

    @property
    def offset(self) -> Optional[str]:
        return self.__offset

    @offset.setter
    def offset(self, val):
        self.__offset = val

    @property
    def unverified_offset(self) -> Optional[str]:
        return self.__unverified_offset

    @unverified_offset.setter
    def unverified_offset(self, val):
        self.__unverified_offset = val

    @property
    def unverified_signature(self) -> Optional[str]:
        return self.__unverified_hash

    @unverified_signature.setter
    def unverified_signature(self, val):
        self.__unverified_hash = val

    @property
    def verified_height(self) -> Optional[int]:
        return self.__verified_height

    @verified_height.setter
    def verified_height(self, val):
        self.__verified_height = val

    @property
    def convertion_ratio(self) -> float:
        return self._convertion_ratio

    @property
    def active(self) -> bool:
        return self.enabled and self.__status == 1

    def _set_current_wallet(self, cw: int):
        if cw != self.__current_wallet:
            self.__current_wallet = cw

    def _get_current_wallet(self) -> int:
        return self.__current_wallet if self.__current_wallet < len(self.__wallet_list) else 0

    def _set_status(self, status: int):
        if status != self.__status:
            self.statusChanged.emit()
            self.__status = status

    def _get_status(self) -> int:
        return self.__status

    @property
    def basename(self) -> str:
        if self._test:
            # TODO: use super instead
            return self.full_name.partition(' ')[0].lower()
        return self.full_name.lower()

    # qml bindings
    @qt_core.Property(bool, notify=visibleChanged)
    def visible(self) -> bool:
        return self.__visible

    @qt_core.Property(int, notify=balanceChanged)
    def balance(self) -> int:
        return self._balance

    @qt_core.Property(str, notify=balanceChanged)
    def balanceHuman(self) -> str:
        return self.balance_human(self._balance)

    @qt_core.Property(str, notify=balanceChanged)
    def fiatBalance(self) -> str:
        # log.warning(f"{self._balance} ==> {self.fiat_amount(self._balance)}")
        return self.fiat_amount(self._balance)

    @qt_core.Property(bool, constant=True)
    def test(self) -> bool:
        return self._test

    @qt_core.Property(str, constant=True)
    def defaultFee(self) -> str:
        return self.balance_human(self._default_fee)

    @qt_core.Property("QVariantList", constant=True)
    def wallets(self) -> List[address.CAddress]:
        if self.show_empty:
            return self.__wallet_list
        return [w for w in self.__wallet_list if w.balance > 0]

    @qt_core.Property(qt_core.QObject, constant=True)
    def addressModel(self) -> qt_core.QObject:
        return self.__address_model

    @property
    def show_empty(self) -> bool:
        return not self.__address_model.emptyFilter

    @show_empty.setter
    def show_empty(self, value=bool) -> None:
        self.__address_model.emptyFilter = not value
        for w in self.__wallet_list:
            w.set_old()

    @qt_core.Property(bool, notify=expandedChanged)
    def expanded(self) -> bool:
        return self.__expanded

    @expanded.setter
    def _set_expanded(self, ex: bool):
        if ex != self.__expanded:
            self.__expanded = ex
            self.expandedChanged.emit()

    @visible.setter
    def _set_visible(self, ex: bool):
        if ex != self.__visible:
            self.__visible = ex
            self.visibleChanged.emit()

    @property
    def address_names(self) -> List[str]:
        """
        all children addresses as list[string]
        it expected to be called very frequently
        """
        return meta.setdefaultattr(self, ADDRESS_NAMES,
                                   [w.name for w in self.__wallet_list])

    def _reset_address_names(self):
        if hasattr(self, ADDRESS_NAMES):
            delattr(self, ADDRESS_NAMES)

    status = qt_core.Property(
        int, _get_status, _set_status, notify=statusChanged)
    height = qt_core.Property(
        int, _get_height, _set_height, notify=heightChanged)

    current_wallet = property(_get_current_wallet, _set_current_wallet)


class BitCoin(CoinType):
    name = "btc"
    full_name = "Bitcoin"
    network = coin_network.BitcoinMainNetwork
    _enabled = True
    _decimal_level = 7
    _hd_index = 0
    _usd_rate = 9400.51
    _btc_rate = 1.


class BitCoinTest(BitCoin):
    name = "btctest"
    full_name = "Bitcoin Test"
    net_name = "btc-testnet"
    network = coin_network.BitcoinTestNetwork
    _test = True
    _usd_rate = 9400.51
    _btc_rate = 1.


class LiteCoin(CoinType):
    name = "ltc"
    full_name = "Litecoin"
    network = coin_network.LitecoinMainNetwork
    _enabled = True
    _decimal_level = 7
    _hd_index = 2
    _usd_rate = 39.83
    _btc_rate = 0.0073
