import itertools
import logging
from typing import Iterable, List, Optional, Union

import PySide2.QtCore as qt_core

from . import address, coin_network, db_entry, hd, key, root_address, \
    serialization
from .. import coins, meta
from ..models.address_list import AddressListModel, AddressListSortedModel
from ..models.coin_list import \
    CoinAmountModel, \
    CoinRemoteStateModel, \
    CoinStateModel
from ..models.tx_list import TxListModel, TxListSortedModel, TxListConcatenateModel

log = logging.getLogger(__name__)



def network_tag(net: coin_network.CoinNetworkBase) -> str:
    return next(c.name for c in CoinType.all if c.network == net)  # pylint: disable=E1133


class CoinType(db_entry.DbEntry, serialization.SerializeMixin):
    rateChanged = qt_core.Signal()

    name: str = None
    _decimal_level: int = 0
    _test: bool = False
    _usd_rate: float = 0.

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
    visibleChanged = qt_core.Signal()
    invalidServer = qt_core.Signal()
    addAddress = qt_core.Signal(address.CAddress)

    @meta.classproperty
    def all(cls) -> Iterable:  # pylint: disable=E0213
        return (val for _, val in globals().items() if isinstance(val, type) and issubclass(val, cls) and val is not cls)

    def __init__(self, parent):
        super().__init__(parent)
        self._address_list = []

        self._balance = 0

        self._remote = {}  # TODO

        self._set_object_name(self.name)
        self.__height = None
        self.__offset = None
        #
        self.__verified_height = None
        self.__unverified_offset = None
        self.__unverified_hash = None
        #
        self.__status = None

        self.__hd_node = None
        self.__visible = True
        self.root = root_address.RootAddress(self)
        self.addAddress.connect(self.addAddressImpl,
                                qt_core.Qt.QueuedConnection)

        from ..ui.gui import Application
        self._amount_model = CoinAmountModel(Application.instance(), self)
        self._state_model = CoinStateModel(Application.instance(), self)
        self._remote_state_model = CoinRemoteStateModel(Application.instance(), self)
        self._address_list_model = AddressListModel(Application.instance(), self)
        self._tx_list_model = TxListConcatenateModel(Application.instance())

    def __str__(self) -> str:
        return f"<{self.fullName},{self.rowid} vis:{self.__visible}>"

    @property
    def amountModel(self) -> CoinAmountModel:
        return self._amount_model

    @property
    def stateModel(self) -> CoinStateModel:
        return self._state_model

    @property
    def remoteStateModel(self) -> CoinRemoteStateModel:
        return self._remote_state_model

    @property
    def addressListModel(self) -> AddressListModel:
        return self._address_list_model

    def addressListSortedModel(self) -> AddressListSortedModel:
        from ..ui.gui import Application
        return AddressListSortedModel(Application.instance(), self._address_list_model)

    @property
    def addressList(self) -> List[address.CAddress]:
        return self._address_list

    @property
    def txListModel(self) -> TxListModel:
        return self._tx_list_model

    def txListSortedModel(self) -> TxListSortedModel:
        from ..ui.gui import Application
        return TxListSortedModel(Application.instance(), self._tx_list_model)

    @qt_core.Property(str, constant=True)
    def unit(self) -> str:
        """
        Coin unit name
        """
        if self._test:
            return self.name[:-4].upper()
        return self.name.upper()

    def balance_human(self, amount: float = None) -> str:
        if amount is None:
            amount = self._balance
        res = amount / (10 ** self._DECIMAL_SIZE)
        res = format(round(res, self._decimal_level), 'f')
        if '.' in res:
            return res.rstrip("0.") or "0"
        return res

    def from_human(self, value: str) -> float:
        return float(value) * 10 ** self._DECIMAL_SIZE

    def fiat_amount(self, amount: float) -> float:
        return amount * self._usd_rate / (10 ** self._DECIMAL_SIZE)

    def _get_rate(self)-> float:
        "USD rate"
        return self._usd_rate

    def _set_rate(self, rt: float):
        if rt == self._usd_rate:
            return
        self._usd_rate = rt
        self.rateChanged.emit()

    rate = qt_core.Property(int, _get_rate, _set_rate, notify=rateChanged)

    def hd_address(self, hd_index: int) -> str:
        if self.__hd_node is None:
            raise address.AddressError(f"There's no private key in {self}")
        return self.__hd_node.make_child_prv(
            hd_index,
            False,
            self.network)

    @qt_core.Slot(address.CAddress)
    def addAddressImpl(self, wallet: address.CAddress) -> None:
        assert qt_core.QThread.currentThread() == self.thread()
        with self._address_list_model.lockInsertRows():
            self._address_list.append(wallet)
            self.update_balance()
        self._tx_list_model.addSourceModel(wallet.txListModel)
        from ..ui.gui import Application
        Application.instance().coinManager.render_cell(self)
        Application.instance().networkThread.update_wallet(wallet)

    def _next_hd_index(self):
        idxs = [a.hd_index for a in self._address_list]
        return next(k for k in itertools.count(1) if k not in idxs)

    def make_address(self, type_: key.AddressType = key.AddressType.P2WPKH, label: str = "", message: str = "") -> address.CAddress:
        """
        create NEW active address ( with keys)
        """
        if self.__hd_node is None:
            raise address.AddressError(f"There's no private key in {self}")
        hd_index = 1
        while any(w.hd_index == hd_index for w in self._address_list):
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
        #if self.parent():
        if True:
            from ..application import CoreApplication
            CoreApplication.instance().databaseThread.save_wallet(wallet)
            self.addAddress.emit(wallet)
        else:
            self.addAddressImpl(wallet)
        return wallet

    def add_watch_address(self, name: str, label: str = "") -> address.CAddress:
        # self(name)
        adr = address.CAddress(name, self, created=True)
        adr.create()
        adr.label = label
        #if self.parent():
        if True:
            self.addAddress.emit(adr)
            from ..application import CoreApplication
            CoreApplication.instance().databaseThread.save_wallet(adr)
        else:
            # for tests
            self.addAddressImpl(adr)
        return adr

    def append_address(self, name: str, *args) -> address.CAddress:
        assert isinstance(name, str), f"name is {type(name)}: {name}"
        """
        make address structure from data.
        """
        has = [n for n in self._address_list if name.strip().casefold() ==
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
            "addresses": [w.to_table() for w in self._address_list],
        }

    def from_table(self, table: dict):
        assert self.name == table["name"]
        self.visible = table["visible"]
        self._address_list.clear()
        for addr_t in table["addresses"]:
            wallet = address.CAddress.from_table(addr_t, self)
            self._address_list.append(wallet)
            self._tx_list_model.addSourceModel(wallet.txListModel)

    @classmethod
    def match(cls, name: str) -> bool:
        "Match coin by string input"
        name_ = name.strip().casefold()
        return name_ in [
            cls.name.casefold(),
            cls.fullName.casefold(),
        ]

    def update_balance(self):
        self._balance = sum(int(w.balance)
                            for w in self._address_list if not w.readOnly)
        self.balanceChanged.emit()
        self._amount_model.refresh()

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

    @property
    def tx_count(self) -> int:
        return sum(len(w) for w in self._address_list)

    def empty(self, skip_zero: bool) -> bool:
        if skip_zero:
            return next((w for w in self._address_list if not w.empty_balance), None) is None
        return not self

    def __iter__(self) -> "CoinType":
        self.__wallet_iter = iter(self._address_list)
        return self

    def __next__(self) -> address.CAddress:
        return next(self.__wallet_iter)

    # abc implemented it but we can do it better
    def __contains__(self, value: Union[str, address.CAddress]) -> bool:
        if not isinstance(value, str):
            value = value.name
        return any(value == add.name for add in self._address_list)

    def __len__(self) -> int:
        return len(self._address_list)

    def __bool__(self) -> bool:
        return bool(self._address_list)

    # don't bind not_empty with addressModel !!! . beware recursion
    def __getitem__(self, key: Union[int, str]) -> address.CAddress:
        if isinstance(key, int):
            return self._address_list[key]
        if isinstance(key, str):
            return next((w for w in self._address_list if w.name == key), None)

    def __update_wallets(self, from_=Optional[int], remove_txs_from: Optional[int] = None, verbose: bool = False):
        "from old to new one !!!"
        for w in self._address_list:
            w.update_tx_list(from_, remove_txs_from, verbose)
        # it must be called when height changed
        # CoreApplication.instance().networkThread.retrieveCoinHistory.emit(coin)

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
        index = self._address_list.index(wallet)
        # self._address_list.remove(wallet)
        self._tx_list_model.removeSourceModel(self._address_list[index].txListModel)
        wallet.clear()
        with self._address_list_model.lockRemoveRows(index):
            del self._address_list[index]
        self.update_balance()

    def clear(self):
        for addr in self._address_list:
            addr.clear()
        self._address_list.clear()
        self.update_balance()

    def _set_height(self, hei: int):
        if hei != self.__height:
            self.__height = hei
            self.heightChanged.emit()  # why no ???

    def _get_height(self) -> int:
        return self.__height

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
    def active(self) -> bool:
        return self.__status == 1

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
            return self.fullName.partition(' ')[0].lower()
        return self.fullName.lower()

    # qml bindings
    @qt_core.Property(bool, notify=visibleChanged)
    def visible(self) -> bool:
        return self.__visible

    @qt_core.Property(int, notify=balanceChanged)
    def balance(self) -> int:
        return self._balance

    @qt_core.Property(str, notify=balanceChanged)
    def fiatBalance(self) -> float:
        return self.fiat_amount(self._balance)

    @qt_core.Property(bool, constant=True)
    def test(self) -> bool:
        return self._test

    @qt_core.Property(str, constant=True)
    def defaultFee(self) -> str:
        return self.balance_human(self._default_fee)

    @qt_core.Property("QVariantList", constant=True)
    def wallets(self) -> List[address.CAddress]:
        return self._address_list

    @visible.setter
    def _set_visible(self, ex: bool):
        if ex != self.__visible:
            self.__visible = ex
            self.visibleChanged.emit()
            self._state_model.refresh()

    status = qt_core.Property(
        int, _get_status, _set_status, notify=statusChanged)
    height = qt_core.Property(
        int, _get_height, _set_height, notify=heightChanged)


class Bitcoin(CoinType, coins.Bitcoin):
    name = "btc"
    network = coin_network.BitcoinMainNetwork
    _decimal_level = 7
    _hd_index = 0
    _usd_rate = 9400.51


class BitcoinTest(Bitcoin, coins.BitcoinTest):
    name = "btctest"
    network = coin_network.BitcoinTestNetwork
    _test = True
    _usd_rate = 9400.51


class Litecoin(CoinType, coins.Litecoin):
    name = "ltc"
    network = coin_network.LitecoinMainNetwork
    _decimal_level = 7
    _hd_index = 2
    _usd_rate = 39.83
