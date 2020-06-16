"""
Qt signals, properties and slots in camel !
"""
import logging
import PySide2.QtCore as qt_core
from typing import List, Iterable, Optional, Union
from . import abs_coin
from . import address
from . import coin_network
from . import key
from . import serialization
from .. import meta
# linter
from . import hd

log = logging.getLogger(__name__)

ADDRESS_NAMES = "__address_names"

# locale.setlocale(locale.LC_ALL, 'en_US.utf8')


class SelectAddressError(Exception):
    pass


def network_tag(net: coin_network.CoinNetworkBase) -> str:
    return next(c.name for c in CoinType.all if c.NETWORK == net)  # pylint: disable=E1133


class CoinType(abs_coin.CoinBase, serialization.SerializeMixin):
    # decimal points
    _default_fee = 10000
    # [[https://github.com/satoshilabs/slips/blob/master/slip-0044.md|SLIP-0044 : Registered coin types for BIP-0044]]
    _hd_index: int = None
    NETWORK: coin_network.CoinNetworkBase = None
    # testnet ID is the same for all coins
    TEST_HD_INDEX = 1
    #
    statusChanged = qt_core.Signal()
    heightChanged = qt_core.Signal()
    balanceChanged = qt_core.Signal()
    expandedChanged = qt_core.Signal()
    walletListChanged = qt_core.Signal()
    visibleChanged = qt_core.Signal()
    invalidServer = qt_core.Signal()

    @meta.classproperty
    def all(cls) -> Iterable:  # pylint: disable=E0213
        return (val for _, val in globals().items() if isinstance(val, type) and issubclass(val, cls) and val is not cls)

    def __init__(self, parent):
        super().__init__(parent=parent)
        self._set_object_name(self.name)
        self._height = None
        self._offset = None
        #
        self._verified_height = None
        self._unverified_offset = None
        self._unverified_signature = None
        #
        self._status = None
        self._wallet_list = []
        self._balance = 0.
        self._current_wallet = 0
        self._hd_node = None
        self._expanded = False
        self._visible = True
        # TODO: bad approach
        self.show_empty = True

    def __str__(self) -> str:
        return f"<{self.full_name},{self.rowid} vis:{self._visible}>"

    def hd_address(self, hd_index: int) -> str:
        if self._hd_node is None:
            raise address.AddressError(f"There's no private key in {self}")
        return self._hd_node.make_child_prv(
            hd_index,
            False,
            self.NETWORK)

    def make_address(self, type_: key.AddressType = key.AddressType.P2WPKH, label: str = "", message: str = "") -> address.CAddress:
        """
        create NEW active address ( with keys)
        """
        if self._hd_node is None:
            raise address.AddressError(f"There's no private key in {self}")
        # big question ?
        # TODO: it is very important difference.
        # hd_index = len(self._wallet_list)
        # hd_index = self._hd_node.children_count
        hd_index = 1
        # but check existing
        while any(w.hd_index == hd_index for w in self._wallet_list):
            hd_index += 1
        new_hd = self._hd_node.make_child_prv(
            # self._hd_node.children_count, ??
            hd_index,
            False,
            self.NETWORK)
        wallet = address.CAddress.make_from_hd(new_hd, self, type_)
        assert wallet.hd_index == hd_index
        wallet.label = label
        wallet._message = message
        log.debug(
            f"New wallet {wallet}  created from HD: {new_hd.chain_path} net:{self.NETWORK}")
        self._wallet_list.append(wallet)
        self._reset_address_names()
        # for tests
        if self.parent():
            # it may be existing address ... then we should update it
            self.parent().update_wallet(wallet)
            self.parent().save_wallet(wallet)
        self.walletListChanged.emit()
        return wallet

    def add_watch_address(self, name: str, label: str) -> address.CAddress:
        adr = address.CAddress(name, self)
        adr.create()
        adr.label = label
        self(adr.name)
        self._wallet_list.append(adr)
        self._reset_address_names()
        self.parent().update_wallet(adr)
        self.parent().save_wallet(adr)
        self.walletListChanged.emit()
        return adr

    def append_address(self, name: str, *args) -> address.CAddress:
        assert isinstance(name, str), f"name is {type(name)}: {name}"
        """
        make address structure from data.
        """
        has = [n for n in self._wallet_list if name.strip().casefold() ==
               n.name.casefold()]
        if has:
            log.warn(f"Address {name} already exists")
            return has[0]
        # invalidate
        self(name)
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
        self._reset_address_names()
        self._wallet_list.append(w)
        self.parent().update_wallet(w)
        self.walletListChanged.emit()
        return w

    def to_table(self) -> dict:
        return {
            "name": self.name,
            "visible": self._visible,
            "addresses": [w.to_table() for w in self._wallet_list],
        }

    def from_table(self, table: dict):
        assert self.name == table["name"]
        self.visible = table["visible"]
        self._wallet_list.clear()
        for addr_t in table["addresses"]:
            wallet = address.CAddress.from_table(addr_t, self)
            self._wallet_list.append(wallet)
        self._reset_address_names()
        self.walletListChanged.emit()

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
        self._balance = sum(int(w.balance) for w in self._wallet_list)
        self.balanceChanged.emit()

    def make_hd_node(self, _parent_node):
        self._hd_node = _parent_node.make_child_prv(
            self.TEST_HD_INDEX if self._test else self._hd_index, True, self.NETWORK)

    @property
    def hd_node(self) -> hd.HDNode:
        return self._hd_node

    @property
    def private_key(self) -> key.PrivateKey:
        if self._hd_node:
            return self._hd_node.key

    def __call__(self, addr: str):
        """
        throws AddressError
        """
        self._validate_address(addr)

    def __iter__(self) -> "CoinType":
        self._wallet_iter = iter(self._wallet_list)
        return self

    def __next__(self) -> address.CAddress:
        return next(self._wallet_iter)

    def __len__(self) -> int:
        return len(self._wallet_list)

    def __getitem__(self, key: Union[int, str]) -> address.CAddress:
        if isinstance(key, int):
            return self._wallet_list[key]
        if isinstance(key, str):
            return next((w for w in self._wallet_list if w.name == key), None)

    def parse(self, data: dict, poll: bool, **kwargs) -> bool:
        """
        poll - regular polling (not at start)

        next cases here:
        - return true to update coin in db
        - emit height changed to update tx list
        - change coin status
        - mark server as invalid
        """

        changed = False
        verified_height = int(data["verified_height"])
        # don't rely on qt meta
        old_height = self._height
        # wrong signature => there's no point to see more, total update
        if self._unverified_signature is None:
            self._verified_heigh = None
            self._height = None
        else:
            # don't clear wht to do exactly
            if self._verified_height and self._verified_height > verified_height:
                log.error(
                    f"server verified height is more than local one. Server is invalid")
                self.invalidServer.emit()
                return False
        offset = data["offset"]
        status = int(data["status"])
        height = int(data["height"])
        unverified_offset = data["unverified_offset"]
        #
        if kwargs.get("verbose"):
            log.warning(f"data {data} uoff:{unverified_offset}")
        if unverified_offset != self._unverified_offset:
            self._offset = unverified_offset
            self._unverified_offset = unverified_offset
            changed = True
        if offset != self._offset:
            self._offset = offset
            changed = True
        if height != self._height:
            self._height = height
            changed = True
        if status != self._status:
            self._status = status
            self.statusChanged.emit()
            changed = changed or status
        if old_height != self._height:
            # to see
            log.debug(
                f"{self} height changed from {old_height} to {self._height}")
            self.heightChanged.emit()
        if changed:
            self._unverified_signature = data["unverified_hash"]
            self._verified_heigh = verified_height
            self._unverified_offset = unverified_offset
        return changed

    def remove_wallet(self, wallet: address.CAddress):
        self._wallet_list.remove(wallet)
        self.update_balance()
        self.walletListChanged.emit()
        self._reset_address_names()

    def clear(self):
        for addr in self._wallet_list:
            addr.clear()
        self._wallet_list.clear()

    def _set_height(self, hei: int):
        if hei != self._height:
            self._height = hei
            self.heightChanged.emit()  # why no ???

    def _get_height(self) -> int:
        return self._height

    @property
    def gcd(self) -> "GCD":
        return self.parent()

    @property
    def offset(self) -> Optional[str]:
        return self._offset

    @offset.setter
    def offset(self, val):
        self._offset = val

    @property
    def unverified_offset(self) -> Optional[str]:
        return self._unverified_offset

    @unverified_offset.setter
    def unverified_offset(self, val):
        self._unverified_offset = val

    @property
    def unverified_signature(self) -> Optional[str]:
        return self._unverified_signature

    @unverified_signature.setter
    def unverified_signature(self, val):
        self._unverified_signature = val

    @property
    def verified_height(self) -> Optional[int]:
        return self._verified_height

    @verified_height.setter
    def verified_height(self, val):
        self._verified_height = val

    @property
    def convertion_ratio(self) -> float:
        return self._convertion_ratio

    @property
    def active(self) -> bool:
        return self.enabled and self._status == 1

    def _set_current_wallet(self, cw: int):
        if cw != self._current_wallet:
            self._current_wallet = cw

    def _get_current_wallet(self) -> int:
        return self._current_wallet if self._current_wallet < len(self._wallet_list) else 0

    def _set_status(self, status: int):
        if status != self._status:
            self.statusChanged.emit()
            self._status = status

    def _get_status(self) -> int:
        return self._status

    @property
    def basename(self) -> str:
        if self._test:
            # TODO: use super instead
            return self.full_name.partition(' ')[0].lower()
        return self.full_name.lower()

    # qml bindings
    @qt_core.Property(bool, notify=visibleChanged)
    def visible(self) -> bool:
        return self._visible

    @qt_core.Property(int, notify=balanceChanged)
    def balance(self) -> int:
        return self._balance

    @qt_core.Property(str, notify=balanceChanged)
    def balanceHuman(self) -> str:
        return self.balance_human(self._balance)

    @qt_core.Property(str, notify=balanceChanged)
    def fiatBalance(self) -> str:
        return self.fiat_amount(self._balance)

    @qt_core.Property(bool, constant=True)
    def test(self) -> bool:
        return self._test

    @qt_core.Property(str, constant=True)
    def defaultFee(self) -> str:
        return self.balance_human(self._default_fee)

    @qt_core.Property("QVariantList", notify=walletListChanged)
    def wallets(self) -> List[address.CAddress]:
        return self._filtered_wallet_list

    @property
    def show_empty(self) -> bool:
        return self.show_empty

    @show_empty.setter
    def show_empty(self, value=bool) -> None:
        self._filtered_wallet_list = self._wallet_list if value else [
            w for w in self._wallet_list if w.balance > 0]
        self._show_empty = value

    @qt_core.Property(bool, notify=expandedChanged)
    def expanded(self) -> bool:
        return self._expanded

    @expanded.setter
    def _set_expanded(self, ex: bool):
        if ex != self._expanded:
            self._expanded = ex
            self.expandedChanged.emit()

    @visible.setter
    def _set_visible(self, ex: bool):
        if ex != self._visible:
            self._visible = ex
            self.visibleChanged.emit()

    @property
    def address_names(self) -> List[str]:
        """
        all children addresses as list[string]
        it expected to be called very frequently
        """
        return meta.setdefaultattr(self, ADDRESS_NAMES,
                                   [w.name for w in self._wallet_list])

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
    NETWORK = coin_network.BitcoinMainNetwork
    _enabled = True
    _decimal_level = 7
    _hd_index = 0
    _usd_rate = 9400.51
    _btc_rate = 1.

    def __init__(self, parent):
        super().__init__(parent=parent)


class BitCoinTest(BitCoin):
    name = "btctest"
    full_name = "Bitcoin Test"
    NETWORK = coin_network.BitcoinTestNetwork
    _test = True
    _usd_rate = 9400.51
    _btc_rate = 1.


class LiteCoin(CoinType):
    name = "ltc"
    full_name = "Litecoin"
    NETWORK = coin_network.LitecoinMainNetwork
    _enabled = True
    _decimal_level = 7
    _hd_index = 2
    _usd_rate = 39.83
    _btc_rate = 0.0073

    def __init__(self, parent):
        super().__init__(parent=parent)


class LiteCoinTest(LiteCoin):
    name = "ltctest"
    full_name = "Litecoin Test"
    NETWORK = coin_network.LitecoinTestNetwork
    _test = True
    _usd_rate = 39.83
    _btc_rate = 0.0073


class EthereumCoin(CoinType):
    name = "eth"
    full_name = "Ethereum"
    _btc_rate = 0.026


class BinanceCoin(CoinType):
    name = "bnb"
    full_name = "Binancecoin"
    _btc_rate = 0.00211


class RippleCoin(CoinType):
    name = "xrp"
    full_name = "Ripple"
    btc_rate = 0.000001


class StellarCoin(CoinType):
    name = "xlm"
    full_name = "Stellar"
    _btc_rate = 0.000007


class TetherCoin(CoinType):
    name = "usdt"
    full_name = "Tether"


class EOSCoin(CoinType):
    name = "eos"
    full_name = "EOS"
