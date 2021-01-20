
import abc
import enum
import io
import json
import logging
import traceback
import sys
from typing import Callable, List, Tuple, Iterable

import PySide2.QtCore as qt_core
import PySide2.QtNetwork as qt_network

from .. import loading_level
from ..wallet import address, coins, hd, key, mtx_impl, mutable_tx, tx
from . import server_error

log = logging.getLogger(__name__)

####################
# temporary flag due to server errors
####################
SILENCE_CHECKS = True


class AbstractNetworkCommand(qt_core.QObject):

    def __init__(self, parent):
        super().__init__(parent=parent)


class FinalMeta(type(qt_core.QObject), type(abc.ABCMeta)):
    pass


class HTTPProtocol(enum.IntEnum):
    GET = enum.auto()
    POST = enum.auto()


class BaseNetworkCommand(AbstractNetworkCommand, metaclass=FinalMeta):
    action = None
    _server_action = None
    # high verbosity
    verbose = False
    # low verbosity
    silenced = False
    host = None
    protocol = HTTPProtocol.GET
    level = loading_level.LoadingLevel.NONE
    _high_priority = False
    _low_priority = False
    # for debugging purposes
    _ltc_filter = True
    unique = False

    def __init__(self, parent, **kwargs):
        super().__init__(parent=parent)
        self.__high_priority = kwargs.pop("high_priority", False)
        self.__low_priority = kwargs.pop("low_priority", False)
        self.level = kwargs.pop("level", loading_level.LoadingLevel.NONE)
        assert not kwargs

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        assert not cls._low_priority or not cls._high_priority
        # no logging
        if True: # e_logger.SILENCE_VERBOSITY:
            cls.verbose = False
            cls.silent = True
        elif cls.verbose:
            cls.silent = False
            print(f"#### verbose network command: {cls.__name__}")

    @property
    def ext(self) -> bool:
        return self.host is not None

    @property
    def is_ltc(self) -> bool:
        if hasattr(self, "_coin"):
            return isinstance(self._coin, coins.Litecoin)
        return False

    @property
    def high_priority(self) -> bool:
        return self._high_priority or self.__high_priority

    @property
    def low_priority(self) -> bool:
        return self._low_priority or self.__low_priority

    @property
    def request_dict(self) -> dict:
        # request properties => just sugar
        if self.high_priority:
            return {
                "priority": qt_network.QNetworkRequest.HighPriority,
            }
        elif self.low_priority:
            return {
                "priority": qt_network.QNetworkRequest.LowPriority,
            }
        return {}

    @property
    def server_action(self) -> str:
        return self._server_action or self.action

    def get_host(self) -> str:
        return self.host

    def get_action(self) -> str:
        return self.action

    @property
    def args(self) -> List[str]:
        return []

    @property
    def args_get(self) -> dict:
        return {}

    @property
    def post_data(self) -> bytes:
        type_, body = self.args_post
        return json.dumps({
            "data": {
                "type": type_,
                "attributes": body,
            }
        }).encode()

    @property
    def args_post(self) -> Tuple[str, dict]:
        return "", {}

    def on_data(self, data):
        if self.verbose:
            log.debug(f'{self}: got data: %f kB', len(data) / 1024.)
        # raise NotImplementedError()

    @abc.abstractmethod
    def on_data_end(self, http_code=200):
        raise NotImplementedError()

    def process_answer(self, data) -> AbstractNetworkCommand:
        if not data:
            raise server_error.EmptyReplyError()
        if not isinstance(data, dict):
            try:
                body = json.loads(data)
            except Exception as ex:
                raise server_error.JsonError(ex)
        else:
            body = data
        try:
            if 'errors' in body:
                return self.handle_errors(body.get('errors'))
            data = body['data']
            if not SILENCE_CHECKS and data['type'] != self.server_action:
                raise server_error.WrongActionError()
            self.process_meta(body['meta'])
            return self.process_attr(data['attributes'])
        except KeyError as ke:
            raise server_error.ContentError(ke) from ke
        "When reply aborted"
        pass

    def process_meta(self, meta):
        timeframe = int(meta['timeframe'])
        assert timeframe > 0
        if timeframe > 1e9:
            log.warn('Server answer has taken more than 1s !!!')

    def output(self, key=None, value=None):
        """
        abstraction layer around dispalying data to user
        if no value - then use key as a title
        if no key - EOF
        """
        if value is None:
            if key is None:
                sys.stdout.write("\n")
                sys.stdout.flush()
            else:
                print(f"{key}")
        else:
            print(f"{key}:\t{value}")

    def handle_errors(self, errors):
        for error in errors:
            self.handle_error(error)

    def handle_error(self, error):
        # self.output(self.tr("Server error"), error.get('detail'))
        log.critical(f"Server error: {error.get('detail')}")

    def connect_(self, _):
        pass

    def __str__(self):
        return self.__class__.__name__

    def drop(self):
        pass

    @property
    def skip(self) -> bool:
        return False


class JsonStreamMixin:
    """
    simple collect data strategy:
    - it wastes memory and we can implement more sufficient algorithm later
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._json = io.BytesIO()

    def on_data(self, data):
        super().on_data(data)
        self._json.write(data)

    def on_data_end(self, http_code):
        try:
            next_ = self.process_answer(self._json.getvalue())
            # important !!! ( for debugging for a while)
            self._json = io.BytesIO()
            return next_
        except server_error.BaseNetError as se:
            HEAD_LEN = 1024
            log.error(f"Processing answer error: {se}. HTTP CODE: {http_code}")
            log.error(
                f"full answer(first {HEAD_LEN} symbols): {self._json.getvalue()[:HEAD_LEN]}")
            log.error(traceback.format_exc(limit=5, chain=True))

    def __len__(self):
        """
            .getbuffer().nbytes - too heavy
            sys.getsizeof(..) -  GC overhead
            remember buffering
        """
        return self._json.__sizeof__()


class ServerSysInfoCommand(JsonStreamMixin, BaseNetworkCommand):
    """
    To retrieve full server description
    """
    action = 'sysinfo'
    level = loading_level.LoadingLevel.NONE

    def __init__(self, parent):
        super().__init__(parent)

    def get_status(self, value):
        if value == 1:
            return self.tr("Active")
        return self.tr("Not working")

    def process_attr(self, table):
        self.output(self.tr("Server name"), table["name"])
        self.output(self.tr("Server version"), table["version"][0])
        self.output(self.tr("Coins:"))
        for coin, data in table["coins"].items():
            self.output(self.tr("Coin name"), coin)
            self.output(self.tr("Daemon version"), data["version"][0])
            self.output(self.tr("Height"), data["height"])
            self.output(self.tr("Status"), self.get_status(data["status"]))


class CheckServerVersionCommand(ServerSysInfoCommand):
    """
    To ensure the server version match client revision.

    For now we just compare it with version from DB
    """
    serverVersion = qt_core.Signal(int, str, arguments=["version", "human"])
    verbose = False
    level = loading_level.LoadingLevel.NONE

    def __init__(self, parent=None):
        super().__init__(parent)

    def process_attr(self, table):
        versions = table["version"][::-1]
        self.serverVersion.emit(*versions)
        from ..ui.gui import Application
        gui_api = Application.instance()
        if gui_api:
            gui_api.uiManager.fill_coin_info_model(table["coins"])

    def connect_(self, gcd):
        super().connect_(gcd)
        self.serverVersion.connect(
            gcd.onServerVersion, qt_core.Qt.QueuedConnection)


class CoinInfoCommand(JsonStreamMixin, BaseNetworkCommand):
    action = "coins"
    level = loading_level.LoadingLevel.NONE

    def __init__(self, parent):
        super().__init__(parent=parent)

    def process_attr(self, table):
        for coin, data in table.items():
            self.output("Coin", coin)
            self.output("Active", data["status"])
            self.output("Offset", data["offset"])
            self.output("Height", data["height"])


class UpdateCoinsInfoCommand(CoinInfoCommand):
    silenced = True
    unique = True
    level = loading_level.LoadingLevel.NONE
    verbose_filter = "ltc"

    def __init__(self, poll: bool, parent=None):
        """
        poll is down on start and then is up on next calls
        """
        super().__init__(parent=parent)
        self._poll = poll

    def process_attr(self, table: dict):
        """
        it is expected to be called frequently
        """
        # log.warning(f"UPDATE COINS RESULT: {table}")
        for coin_name, data in table.items():
            verbose = self.verbose and coin_name == self.verbose_filter
            if verbose:
                log.warning(f"{coin_name} => {data}")
            coin = self._gcd[coin_name]
            # don't swear here. we've sworn already
            if coin is not None and coin.parse_coin(data, self._poll, verbose=verbose):
                """
                important scope here
                """
                if verbose:
                    log.debug(f"remote {coin} changed . poll: {self._poll}")
                from ..application import CoreApplication
                CoreApplication.instance().databaseThread.saveCoin.emit(coin)
            elif verbose:
                log.debug(f"{coin} hasn't changed")

    def __str__(self):
        return super().__str__() + f"[poll={self._poll}]"


class AddressInfoCommand(JsonStreamMixin, BaseNetworkCommand):
    action = "coins"
    _server_action = "address"
    level = loading_level.LoadingLevel.ADDRESSES

    def __init__(self, wallet: address.CAddress, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self._wallet = wallet

    @property
    def args(self):
        return [self._wallet.coin.name, self._wallet.name]

    def process_attr(self, table):
        self.output(self.tr("Coin type"), table["type"])
        self.output(self.tr("Address"), table["address"])
        self.output(self.tr("Transaction count"),
                    table["number_of_transactions"])
        self.output(self.tr("Balance"), table["balance"])

    def __str__(self):
        return f"{self.__class__.__name__}: {self._wallet.name}"


class ValidateAddressCommand(JsonStreamMixin, BaseNetworkCommand):
    action = "coins"
    _server_action = "address"
    level = loading_level.LoadingLevel.NONE
    _high_priority = True

    def __init__(self, coin: coins.CoinType, address: str, callback: Callable[[bool], None], parent):
        super().__init__(parent=parent)
        self._coin = coin
        self._address = address
        self._callback = callback

    @property
    def args(self):
        return [self._coin.name, self._address]

    def process_attr(self, table):
        self._callback(table["address"] == self._address)

    def handle_errors(self, errors):
        self._callback(False)

    def __str__(self):
        return f"{self.__class__.__name__}: {self._address}"


class LookForHDAddresses(AddressInfoCommand):
    """
    search all HD addresses with non zero balances
    we stop search when ew meet unexistent address
    """
    MAX_EMPTY_NUMBER = 6
    level = loading_level.LoadingLevel.ADDRESSES
    verbose = False
    _low_priority = True
    silenced = True

    def __init__(self, coin: coins.CoinType, parent, hd_index=0, empty_count: int = 0, segwit: bool = True, hd_: hd.HDNode = None):
        super().__init__(None, parent=parent)
        try:
            self._coin = coin
            self._hd_index = hd_index
            self._empty_count = empty_count
            self._segwit = segwit
            self._hd: hd.HDNode = hd_ or coin.hd_address(hd_index)
            self._address: str = self._hd.to_address(
                key.AddressType.P2WPKH if segwit else key.AddressType.P2PKH)
            while self._address in self._coin:
                if self.verbose:
                    log.warning(f"address exists :{self._address}")
                self._empty_count = 0
                if self._segwit:
                    self._segwit = False
                    self._address = self._hd.to_address(key.AddressType.P2PKH)
                else:
                    self._hd_index += 1
                    self._hd = coin.hd_address(self._hd_index)
                    self._address = self._hd.to_address(key.AddressType.P2WPKH)

        except address.AddressError as ae:
            # TODO:
            log.error(f"error {ae}")
            self._address = None

    @property
    def args(self):
        return [self._coin.name, self._address]

    def process_attr(self, table):
        assert self._address == table["address"]
        if self.verbose and self.is_ltc:
            log.warning(f"{self._empty_count}: {table}")
        if table["balance"] == 0 and table["number_of_transactions"] == 0:
            self._empty_count += 1
            if self._empty_count > self.MAX_EMPTY_NUMBER * 2:  # remember SW + no SW
                return None
        else:
            self._empty_count = 0
            # TODO: we can provide some information to new address
            wallet = self._coin.append_address(self._address)
            wallet.set_prv_key(self._hd)
            log.debug(
                f"New no empty address found: {wallet}")
        return next(self)

    def exists(self) -> bool:
        return self._address in self._coin

    def __next__(self):
        if self._segwit:
            return LookForHDAddresses(self._coin, self, hd_index=self._hd_index, empty_count=self._empty_count, segwit=False, hd_=self._hd)
        return LookForHDAddresses(self._coin, self, hd_index=self._hd_index + 1, empty_count=self._empty_count)

    def __str__(self):
        return f"{self.__class__.__name__}: {self._coin} IDX:{self._hd_index} SW:{self._segwit}: {self._address}"


class UpdateAddressInfoCommand(AddressInfoCommand):
    """
    Similar to adressInfo but takes wallet and updates it's info without displaying it
    Also it tries to download missed transactions
    """
    action = "coins"
    _server_action = "address"
    verbose = False
    silenced = True
    level = loading_level.LoadingLevel.TRANSACTIONS

    def __init__(self, wallet: address.CAddress, parent = None, **kwargs):
        super().__init__(wallet, parent=parent, high_priority=True, **kwargs)

    @property
    def args(self):
        return [self._wallet.coin.name, self._wallet.name]

    def process_attr(self, table):
        assert self._wallet.name == table["address"]
        if self.verbose:
            log.warning(table)
        # type important!! do not remove
        type_ = table["type"]
        txCount = table["number_of_transactions"]
        balance = table["balance"]
        if balance != self._wallet.balance or \
                txCount != self._wallet.txCount or \
                type_ != self._wallet.type:
            self._wallet.type = type_
            self._wallet.balance = balance
            self._wallet.txCount = txCount
            from ..application import CoreApplication
            CoreApplication.instance().databaseThread.save_wallet(self._wallet)
            diff = txCount - self._wallet.realTxCount
            if diff > 0 and not self._wallet.is_going_update:
                log.debug("Need to download more %s tx for %s",
                          diff, self._wallet)
                return AddressHistoryCommand(self._wallet, parent=self,  high_priority=True)


class AddressHistoryCommand(AddressInfoCommand):
    """
    """
    action = "coins"
    _server_action = "history"
    level = loading_level.LoadingLevel.TRANSACTIONS

    verbose = False
    __prev_wallet = None
    DEFAULT_LIMIT = 50

    def __init__(self, wallet: address.CAddress,
                 limit: int = None,
                 tx_count: int = 0,
                 parent: qt_core.QObject = None,
                 first_offset: int = None,
                 forth: bool = True,
                 **kwargs
                 ):
        super().__init__(wallet, parent, **kwargs)
        # don't touch it!!!!!!!!!!!!!!!!!!! crucial meaning
        self._wallet.is_going_update = True
        self.__forth = forth
        if self.__prev_wallet and self.__prev_wallet.name != wallet.name:
            self.__prev_wallet.is_going_update = False
            self.__prev_wallet.isUpdating = False
        self.__prev_wallet = wallet
        if forth:
            self.__first_offset = first_offset or 'best'
            self.__last_offset = wallet.first_offset
        else:
            self.__first_offset = wallet.last_offset
            self.__last_offset = 'base'
        if not self.__last_offset or self.__last_offset in ['best', 'None']:
            self.__last_offset = 'base'
        self.__limit = limit
        self.__tx_count = tx_count
        if self.verbose:
            log.debug(
                f"request: FORTH:{self.__forth} first off:{self.__first_offset} last off:{self.__last_offset}")

    def process_attr(self, table):
        assert table.get("address") == self._wallet.name
        if self.verbose:
            log.debug(
                f"answer: first off:{table['first_offset']} last off:{table['last_offset']}")
        last_offset = table["last_offset"]
        # beware getter!
        self._wallet.last_offset = last_offset
        if self.__forth and self.__first_offset == 'best':
            self._wallet.first_offset = table["first_offset"]
        self._wallet.last_offset = last_offset
        # use setter !!!
        self.__process_transactions(table["tx_list"])
        #  - we have to save new wallet offsets ?? .. cause app can be closed before next net calls
        from ..application import CoreApplication
        CoreApplication.instance().databaseThread.save_wallet(self._wallet, 500)
        ###
        qt_core.QCoreApplication.processEvents()
        # self._wallet.isUpdating = False
        if self.__limit is None or self.tx_count < self.__limit:
            if self.__forth and last_offset is not None:
                log.debug(f"Next FORTH history request for {self._wallet!r}")
                return self.clone(last_offset)
            elif self.__forth or last_offset is not None:
                log.debug(f"Next BACK history request for {self._wallet!r}")
                return self.clone(forth=False)
        self._wallet.is_going_update = False
        self._wallet.isUpdating = False

    def clone(self, first_offset=None, forth=True):
        return self.__class__(
            wallet=self._wallet,
            limit=self.__limit,
            tx_count=self.__tx_count,
            first_offset=first_offset,
            forth=forth,
            parent=self,
        )

    def on_data(self, data):
        # too much prints
        # super().on_data(data)
        self._json.write(data)

    @ property
    def args(self):
        self._wallet.isUpdating = True
        return [self._wallet.coin.name, self._wallet.name, self._server_action]

    @ property
    def tx_count(self):
        return self.__tx_count

    @ property
    def args_get(self):
        get = {}
        if self.__first_offset is not None and self.__first_offset != 'None':
            get.update({
                "first_offset": self.__first_offset,
            })
        if self.__limit is not None:
            if self.__limit - self.tx_count < self.DEFAULT_LIMIT:
                get.update({
                    "limit": self.__limit - self.tx_count,
                })
        if self.__last_offset is not None:
            get.update({
                "last_offset": self.__last_offset,
            })
        if self.verbose:
            log.info(f"get history opts: {get}  me:{id(self)}")
        return get

    def __process_transactions(self, txs: dict):
        tx_list = [tx.Transaction(self._wallet).parse(*a) for a in txs.items()]
        # strict order !!

        # raw count
        self.__tx_count += len(tx_list)
        self._wallet.add_tx_list(
            tx_list, check_new=self.__forth and self.__first_offset == 'best')
        # lsit updated !!
        if tx_list:
            from ..application import CoreApplication
            CoreApplication.instance().databaseThread.save_tx_list(self._wallet, tx_list)

    @ property
    def skip(self) -> bool:
        return self._wallet.deleted

    def __str__(self):
        return f"<{super().__str__()}> [wallet={self._wallet} foff:{self.__first_offset}]"


class AddressMempoolCommand(AddressInfoCommand):
    verbose = False
    _server_action = "unconfirmed"
    MAX_TIMES = 6
    WAIT_CHUNK = 100
    WAIT_TIMEOUT = 3000
    level = loading_level.LoadingLevel.ADDRESSES
    _high_priority = True

    def __init__(self, wallet: address.CAddress, parent, counter=0):
        super().__init__(wallet, parent=parent)
        self._counter = counter

    @ property
    def args(self):
        return [self._wallet.coin.name, self._wallet.name, self._server_action]

    def process_attr(self, table):
        # TODO: process hash

        txs = table["tx_list"]
        # if no TX here - then wait and check again
        if not txs:
            if self._counter > self.MAX_TIMES:
                log.warning("mempool is empty !!!")
                return
            # sleep for a bit
            to = self.WAIT_TIMEOUT
            while to >= 0:
                to -= self.WAIT_CHUNK
                qt_core.QThread.currentThread().msleep(self.WAIT_CHUNK)
                qt_core.QCoreApplication.processEvents()
            return AddressMempoolCommand(self._wallet, self, counter=self._counter + 1)
        self.__process_transactions(txs)

    def __process_transactions(self, txs: dict):
        for name, body in txs.items():
            # tx = coins.Transaction(self._wallet) WRONG THREAD!
            tx_ = tx.Transaction(self._wallet)
            tx_.parse(name, body)
            try:
                self._wallet.add_tx(tx_, check_new=True)
                from ..application import CoreApplication
                CoreApplication.instance().databaseThread.saveTx.emit(tx_)
            except tx.TxError as txe:
                if self.verbose:
                    log.warn(f"{txe}")


class AbstractMultyMempoolCommand(JsonStreamMixin, BaseNetworkCommand):
    action = "coins"
    _server_action = "unconfirmed"
    protocol = HTTPProtocol.POST
    level = loading_level.LoadingLevel.ADDRESSES

    def __init__(self, wallet_list: Iterable[address.CAddress], parent, hash_=None):
        super().__init__(parent=parent)
        self._wallet_list = list(wallet_list)
        self._hash = hash_

    @ property
    def skip(self) -> bool:
        return not self._wallet_list

    @ property
    def args(self):
        return [self._coin.name, self._server_action]

    @ property
    def skip(self) -> bool:
        return not self._wallet_list

    @ property
    def args_post(self) -> Tuple[str, dict]:
        table = {
            "address_list": [addr.name for addr in self._wallet_list],
        }
        if self._hash:
            table["last_hash"] = self._hash
        return self._server_action, table


class AddressMultyMempoolCommand(AbstractMultyMempoolCommand):
    """
    command to monitor mempool for detecting new just made tx
    """
    verbose = False
    MAX_TIMES = 5
    WAIT_CHUNK = 100
    WAIT_TIMEOUT = 3000
    _high_priority = True

    def __init__(self, wallet_list: List[address.CAddress], parent, counter=0, hash_=None):
        super().__init__(wallet_list=wallet_list, parent=parent, hash_=hash_)
        self.__counter = counter
        self._coin = wallet_list[0].coin

    def process_attr(self, table):
        if self.verbose:
            log.warning(table)

        txs = table["tx_list"]
        self._hash = table["hash"]
        if txs:
            self.__counter += 1
            self.__process_transactions(txs)
        return self.__send_again()

    def __process_transactions(self, txs: dict):
        for name, body in txs.items():
            if self.verbose:
                log.debug(body)
            self.__process_transaction(name, body)

    def __process_transaction(self, name: str, body: dict) -> None:
        # remember!! address not in tx -> in inputs && outputs!!
        for inp in body["input"] + body["output"]:
            w = self._coin[inp["address"]]
            if w is not None:
                tx_ = tx.Transaction(w)
                tx_.parse(name, body)
                tx_.height = w.coin.height + 1
                try:
                    w.add_tx(tx_, check_new=True)
                except tx.TxError as txe:
                    # everythig's good !!!
                    from ..application import CoreApplication
                    CoreApplication.instance().databaseThread.saveTx.emit(tx_)
                    CoreApplication.instance().networkThread.updateTxStatus.emit(tx_)
                    if self.verbose:
                        log.warn(f"{txe}")
                return True

    def __send_again(self):
        if self.verbose:
            log.debug(f"sleep and check mempool again; {self.__counter}")
        if self.__counter <= self.MAX_TIMES:
            to = self.WAIT_TIMEOUT
            while to >= 0:
                to -= self.WAIT_CHUNK
                qt_core.QThread.currentThread().msleep(self.WAIT_CHUNK)
                qt_core.QCoreApplication.processEvents()
            return AddressMultyMempoolCommand(self._wallet_list, self, counter=self.__counter, hash_=self._hash)

    def on_data_end(self, http_code):
        if http_code == 304:
            return self.__send_again()
        return super().on_data_end(http_code)

    @ property
    def counter(self) -> int:
        return self.__counter


class MempoolMonitorCommand(AbstractMultyMempoolCommand):
    verbose = True

    def __init__(self, coin: coins.CoinType, parent, hash_=None):
        super().__init__(wallet_list=iter(coin), parent=parent, hash_=hash_)
        self._coin = coin

    def on_data_end(self, http_code):
        if http_code == 304:
            return None
        return super().on_data_end(http_code)

    def process_attr(self, table):
        if self.verbose:
            log.warning(table)

        self._hash = table["hash"]
        for name, body in table["tx_list"].items():
            if self.verbose:
                log.debug(body)
            self.__process_transaction(name, body)

    def __process_transaction(self, name: str, body: dict) -> None:
        for inp in body["input"] + body["output"]:
            w = self._coin[inp["address"]]
            if w is not None:
                tx_ = tx.Transaction(w)
                tx_.parse(name, body)
                tx_.height = w.coin.height + 1
                try:
                    w.add_tx(tx_, check_new=True)
                except tx.TxError as txe:
                    if self.verbose:
                        log.warn(f"{txe}")


class AddressUnspentCommand(AddressInfoCommand):
    action = "coins"
    _server_action = "unspent"
    level = loading_level.LoadingLevel.NONE
    _high_priority = True
    verbose = False

    def __init__(self, wallet: address.CAddress, first_offset=None,
                 last_offset=None, unspent=None, calls: int = 0, parent=None):
        super().__init__(wallet, parent)
        self.__first_offset = first_offset
        self.__last_offset = last_offset
        self._unspent = unspent or []
        self._calls = calls

    @ property
    def args(self):
        return [self._wallet.coin.name, self._wallet.name, self._server_action]

    @ property
    def args_get(self):
        get = {}
        if self.__first_offset is not None:
            get.update({
                "first_offset": self.__first_offset,
            })
        if self.__last_offset is not None:
            get.update({
                "last_offset": self.__last_offset,
            })
        return get

    def process_attr(self, table):
        assert table.get("address") == self._wallet.name
        last_offset = table["last_offset"]
        if self.verbose:
            log.debug("TX IN ANSWER %d ,%s", len(table["tx_list"]), self)
        self._unspent += table["tx_list"]
        if last_offset is not None:
            if self.verbose:
                log.debug(f"Next history request for {self._wallet}")
            return self.clone(last_offset)
        else:
            self.__process_transactions()

    def clone(self, first_offset):
        return self.__class__(
            wallet=self._wallet,
            unspent=self._unspent,
            first_offset=first_offset,
            calls=self._calls + 1,
        )

    def __process_transactions(self):
        # map it to separate logic layers
        if self.verbose:
            log.debug(
                f"UNSPENT COUNT: {len(self._unspent)} from {self._calls} calls")
        self._wallet.process_unspents(self._unspent)


class BroadcastTxCommand(JsonStreamMixin, BaseNetworkCommand):
    action = "coins"
    protocol = HTTPProtocol.POST
    verbose = False
    level = loading_level.LoadingLevel.NONE
    _high_priority = True

    def __init__(self, mtx: mutable_tx.MutableTransaction, parent):
        super().__init__(parent)
        self._mtx = mtx

    @ property
    def args(self):
        return [self._mtx.coin.name, "tx"]

    def process_attr(self, table):
        tx_id = table["tx"]
        if tx_id != self._mtx.tx_id:
            log.error(
                f"server gives TXID:{tx_id} but sent TXID:{self._mtx.tx_id}")
        elif self.verbose:
            log.debug("Broadcasted TX hash is fine!")
        self._mtx.send_callback(True)

    @ property
    def args_post(self):
        return ("tx_broadcast", {
            "data": str(self._mtx),
        })

    def handle_error(self, error):
        log.error(error)
        err_code = error["code"]
        if server_error.ServerErrorCode.broadcastError == int(err_code):
            self._mtx.send_callback(False, str(error["detail"]))
        else:
            raise server_error.UnknownErrorCode(err_code)


class ExtHostCommand(JsonStreamMixin, BaseNetworkCommand):
    def process_answer(self, data):
        if not data:
            raise server_error.EmptyReplyError()
        if not isinstance(data, dict):
            try:
                body = json.loads(data)
            except Exception:
                raise server_error.JsonError(ex)
        else:
            body = data
        self.process_attr(body)


class GetCoinRatesCommand(ExtHostCommand):
    """
    To retrieve coin rates
    https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd
    """
    DEF_ACTION = "price"
    DEF_HOST = "https://api.coingecko.com/api/v3/simple/"
    CURRENCY = "usd"
    verbose = False
    unique = True

    def __init__(self, parent=None, ):
        super().__init__(parent)
        self._source = None
        from ..ui.gui import Application
        api_ = Application.instance()
        if api_:
            self._source = api_.settingsManager.rateSource

    @ property
    def args_get(self):
        self._coins = self._gcd.all_enabled_coins
        if self._source:
            return self._source.get_arguments(self._coins, self.CURRENCY)
        coins_ = ",".join([c.basename for c in self._coins])
        return {
            "ids": coins_,
            "vs_currencies": self.CURRENCY,
        }

    def get_host(self):
        if self._source:
            return self._source.api_url
        return self.DEF_HOST

    def get_action(self):
        if self._source:
            return self._source.action
        return self.DEF_ACTION

    def process_attr(self, table):
        if self._source:
            self._source.process_result(self._coins, self.CURRENCY, table)
        else:
            for coin in self._coins:
                coin.rate = table[coin.basename][self.CURRENCY]


class GetRecommendFeeCommand(ExtHostCommand):
    "https://bitcoinfees.earn.com/api"
    host = "https://bitcoinfees.earn.com/api/v1/fees/"
    action = "recommended"
    unique = True

    def process_attr(self, table):
        stats = [
            ("fastestFee", 10),
            ("halfHourFee", 30),
            ("hourFee", 60),
        ]
        from ..ui.gui import Application
        Application.instance().feeManager.add_fees(
            {table[to_str]: to_int for to_str, to_int in stats})
