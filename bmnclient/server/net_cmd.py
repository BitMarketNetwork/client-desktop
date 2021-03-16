from __future__ import annotations

import io
import json
import logging
import sys
import traceback
from enum import Enum, auto
from typing import Iterable, List, Optional, Tuple

import PySide2.QtCore as qt_core
import PySide2.QtNetwork as qt_network
from PySide2.QtCore import QObject

from . import server_error
from .. import loading_level
from ..logger import Logger
from ..network.server_parser import ServerCoinParser
from ..wallet import address, coins, hd, key, mutable_tx
from ..wallet.tx import Transaction, TxError

log = logging.getLogger(__name__)

####################
# temporary flag due to server errors
####################
SILENCE_CHECKS = True


class HttpMethod(Enum):
    GET = auto()
    POST = auto()


class BaseNetworkCommand(QObject):
    _BASE_URL = None
    _METHOD = HttpMethod.GET

    @property
    def url(self) -> str:
        return self._BASE_URL

    @property
    def method(self) -> HttpMethod:
        return self._METHOD

    @property
    def statusCode(self) -> Optional[int]:
        return self.__status_code

    @statusCode.setter
    def statusCode(self, value: int):
        if self.__status_code is None:
            self.__status_code = value
        else:
            AttributeError("status is already set.")

    def createRequestData(self) -> Optional[dict]:
        return {}

    def onResponseData(self, data: bytes) -> bool:
        raise NotImplementedError

    def onResponseFinished(self) -> None:
        raise NotImplementedError

    action = None
    _server_action = None
    # high verbosity
    verbose = False
    # low verbosity
    silenced = False
    level = loading_level.LoadingLevel.NONE
    _high_priority = False
    _low_priority = False
    unique = False

    def __init__(self, parent=None, **kwargs) -> None:
        super().__init__(parent=parent)
        self._logger = Logger.getClassLogger(__name__, self.__class__)
        self.__status_code: Optional[int] = None

        self.__high_priority = kwargs.pop("high_priority", False)
        self.__low_priority = kwargs.pop("low_priority", False)
        self.level = kwargs.pop("level", loading_level.LoadingLevel.NONE)
        assert not kwargs

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        assert not cls._low_priority or not cls._high_priority
        cls.verbose = False
        cls.silent = True

    @property
    def ext(self) -> bool:
        return self._BASE_URL is not None

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

    def get_action(self) -> str:
        return self.action

    @property
    def args(self) -> List[str]:
        return []

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

    def process_answer(self, data) -> BaseNetworkCommand:
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
        # when reply aborted
        pass

    def process_meta(self, meta):
        timeframe = int(meta['timeframe'])
        assert timeframe > 0
        if timeframe > 1e9:
            log.warn('Server answer has taken more than 1s !!!')

    def process_attr(self, table):
        pass

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

    @property
    def skip(self) -> bool:
        return False


class JsonStreamMixin:
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._json = io.BytesIO()

    def onResponseData(self, data) -> bool:
        self._json.write(data)
        return True

    def onResponseFinished(self) -> None:
        http_error = self.statusCode
        if not (http_error < 400 or http_error == 500 or http_error == 404):
            return
        try:
            next_ = self.process_answer(self._json.getvalue())
            # important !!! ( for debugging for a while)
            self._json = io.BytesIO()
            if next_:
                from ..ui.gui import CoreApplication
                CoreApplication.instance().networkThread.network.push_cmd(next_)
        except server_error.BaseNetError as se:
            HEAD_LEN = 1024
            log.error(f"Processing answer error: {se}. HTTP CODE: TODO")
            log.error(
                f"full answer(first {HEAD_LEN} symbols): {self._json.getvalue()[:HEAD_LEN]}")
            log.error(traceback.format_exc(limit=5, chain=True))

    def __len__(self):
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
    verbose = False
    level = loading_level.LoadingLevel.NONE

    def __init__(self, parent=None):
        super().__init__(parent)

    def process_attr(self, table):
        versions = table["version"][::-1]
        log.debug(f"server version {versions[0]} / {versions[1]}")
        from ..ui.gui import Application
        gui_api = Application.instance()
        if gui_api:
            gui_api.uiManager.serverVersion = versions[1]
            gui_api.uiManager.fill_coin_info_model(table["coins"])


class UpdateCoinsInfoCommand(JsonStreamMixin, BaseNetworkCommand):
    action = "coins"
    level = loading_level.LoadingLevel.NONE
    silenced = True
    unique = True

    def __init__(self, poll: bool, parent=None):
        super().__init__(parent=parent)
        self._poll = poll

    def process_attr(self, table: dict):
        from ..application import CoreApplication
        for coin in CoreApplication.instance().coinList:
            response = table.get(coin.shortName)
            state_hash = coin.stateHash
            if response and ServerCoinParser.parse(response, coin):
                if coin.stateHash != state_hash:
                    CoreApplication.instance().databaseThread.saveCoin.emit(coin)
                    for a in coin.addressList:
                        self._run_cmd(UpdateAddressInfoCommand(a, self.parent()))


class AddressInfoCommand(JsonStreamMixin, BaseNetworkCommand):
    action = "coins"
    _server_action = "address"
    level = loading_level.LoadingLevel.ADDRESSES

    def __init__(self, wallet: address.CAddress, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self._address = wallet

    @property
    def args(self):
        return [self._address.coin.name, self._address.name]

    def process_attr(self, table):
        self.output(self.tr("Coin type"), table["type"])
        self.output(self.tr("Address"), table["address"])
        self.output(self.tr("Transaction count"),
                    table["number_of_transactions"])
        self.output(self.tr("Balance"), table["balance"])

    def __str__(self):
        return f"{self.__class__.__name__}: {self._address.name}"


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
            while self._address in self._coin.addressList:
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
        if table["balance"] == 0 and table["number_of_transactions"] == 0:
            self._empty_count += 1
            if self._empty_count > self.MAX_EMPTY_NUMBER * 2:  # remember SW + no SW
                return None
        else:
            self._empty_count = 0
            # TODO: we can provide some information to new address
            wallet = address.CAddress(self._address, self._coin)
            wallet.create()
            self._coin.appendAddress(wallet)
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
        return [self._address.coin.name, self._address.name]

    def process_attr(self, table):
        assert self._address.name == table["address"]
        if self.verbose:
            log.warning(table)
        # type important!! do not remove
        type_ = table["type"]
        txCount = table["number_of_transactions"]
        balance = table["balance"]
        if balance != self._address.balance or \
                txCount != self._address.txCount or \
                type_ != self._address.type:
            self._address.type = type_
            self._address.balance = balance
            self._address.txCount = txCount
            from ..application import CoreApplication
            CoreApplication.instance().databaseThread.save_address(self._address)
            diff = txCount - self._address.realTxCount
            if diff > 0 and not self._address.is_going_update:
                log.debug("Need to download more %s tx for %s",
                          diff, self._address)
                return AddressHistoryCommand(self._address, parent=self,  high_priority=True)


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
        self._address.is_going_update = True
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
        assert table.get("address") == self._address.name
        if self.verbose:
            log.debug(
                f"answer: first off:{table['first_offset']} last off:{table['last_offset']}")
        last_offset = table["last_offset"]
        # beware getter!
        self._address.last_offset = last_offset
        if self.__forth and self.__first_offset == 'best':
            self._address.first_offset = table["first_offset"]
        self._address.last_offset = last_offset
        # use setter !!!
        self.__process_transactions(table["tx_list"])
        #  - we have to save new wallet offsets ?? .. cause app can be closed before next net calls
        from ..application import CoreApplication
        CoreApplication.instance().databaseThread.save_address(self._address, 500)
        ###
        qt_core.QCoreApplication.processEvents()
        # self._address.isUpdating = False
        if self.__limit is None or self.tx_count < self.__limit:
            if self.__forth and last_offset is not None:
                log.debug(f"Next FORTH history request for {self._address!r}")
                return self.clone(last_offset)
            elif self.__forth or last_offset is not None:
                log.debug(f"Next BACK history request for {self._address!r}")
                return self.clone(forth=False)
        self._address.is_going_update = False
        self._address.isUpdating = False

    def clone(self, first_offset=None, forth=True):
        return self.__class__(
            wallet=self._address,
            limit=self.__limit,
            tx_count=self.__tx_count,
            first_offset=first_offset,
            forth=forth,
            parent=self,
        )

    def onResponseData(self, data) -> bool:
        self._json.write(data)
        return True

    @property
    def args(self):
        self._address.isUpdating = True
        return [self._address.coin.name, self._address.name, self._server_action]

    @property
    def tx_count(self):
        return self.__tx_count

    def createRequestData(self) -> Optional[dict]:
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
        tx_list = [Transaction(self._address).parse(*a) for a in txs.items()]
        # strict order !!

        # raw count
        self.__tx_count += len(tx_list)
        for tx in tx_list:
            if self._address.appendTx(tx) and self.__forth and self.__first_offset == 'best':
                from ..ui.gui import Application
                Application.instance().uiManager.process_incoming_tx(tx)

        # lsit updated !!
        if tx_list:
            from ..application import CoreApplication
            CoreApplication.instance().databaseThread.save_tx_list(self._address, tx_list)

    @property
    def skip(self) -> bool:
        return self._address.deleted

    def __str__(self):
        return f"<{super().__str__()}> [wallet={self._address} foff:{self.__first_offset}]"


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

    @property
    def args(self):
        return [self._address.coin.name, self._address.name, self._server_action]

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
            return AddressMempoolCommand(self._address, self, counter=self._counter + 1)
        self.__process_transactions(txs)

    def __process_transactions(self, txs: dict):
        for name, body in txs.items():
            # tx = coins.Transaction(self._address) WRONG THREAD!
            tx_ = Transaction(self._address)
            tx_.parse(name, body)
            try:
                self._address.appendTx(tx_)
                from ..ui.gui import Application
                Application.instance().uiManager.process_incoming_tx(tx_)
                Application.instance().databaseThread.saveTx.emit(tx_)
            except TxError as txe:
                if self.verbose:
                    log.warn(f"{txe}")


class AbstractMultyMempoolCommand(JsonStreamMixin, BaseNetworkCommand):
    _METHOD = HttpMethod.POST

    action = "coins"
    _server_action = "unconfirmed"
    level = loading_level.LoadingLevel.ADDRESSES

    def __init__(self, wallet_list: Iterable[address.CAddress], parent, hash_=None):
        super().__init__(parent=parent)
        self._wallet_list = list(wallet_list)
        self._hash = hash_

    @property
    def skip(self) -> bool:
        return not self._wallet_list

    @property
    def args(self):
        return [self._coin.name, self._server_action]

    @property
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
        self.__send_again()

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
                tx_ = Transaction(w)
                tx_.parse(name, body)
                tx_.height = w.coin.height + 1
                try:
                    w.appendTx(tx_)
                    from ..ui.gui import Application
                    Application.instance().uiManager.process_incoming_tx(tx_)
                except TxError as txe:
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

            cmd = AddressMultyMempoolCommand(
                self._wallet_list,
                self,
                counter=self.__counter,
                hash_=self._hash)
            from ..ui.gui import CoreApplication
            CoreApplication.instance().networkThread.network.push_cmd(cmd)

    def onResponseFinished(self) -> None:
        if self.statusCode == 304:
            self.__send_again()
        super().onResponseFinished()

    @property
    def counter(self) -> int:
        return self.__counter


class MempoolMonitorCommand(AbstractMultyMempoolCommand):
    verbose = True

    def __init__(self, coin: coins.CoinType, parent, hash_=None):
        super().__init__(wallet_list=iter(coin.addressList), parent=parent, hash_=hash_)
        self._coin = coin

    def onResponseFinished(self) -> None:
        if self.statusCode != 304:
            super().onResponseFinished()

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
                tx_ = Transaction(w)
                tx_.parse(name, body)
                try:
                    w.appendTx(tx_)
                    from ..ui.gui import Application
                    Application.instance().uiManager.process_incoming_tx(tx_)
                except TxError as txe:
                    if self.verbose:
                        log.warning(f"{txe}")


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

    @property
    def args(self):
        return [self._address.coin.name, self._address.name, self._server_action]

    def createRequestData(self) -> Optional[dict]:
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
        assert table.get("address") == self._address.name
        last_offset = table["last_offset"]
        if self.verbose:
            log.debug("TX IN ANSWER %d ,%s", len(table["tx_list"]), self)
        self._unspent += table["tx_list"]
        if last_offset is not None:
            if self.verbose:
                log.debug(f"Next history request for {self._address}")
            return self.clone(last_offset)
        else:
            self.__process_transactions()

    def clone(self, first_offset):
        return self.__class__(
            wallet=self._address,
            unspent=self._unspent,
            first_offset=first_offset,
            calls=self._calls + 1,
        )

    def __process_transactions(self):
        # map it to separate logic layers
        if self.verbose:
            log.debug(
                f"UNSPENT COUNT: {len(self._unspent)} from {self._calls} calls")
        self._address.process_unspents(self._unspent)


class BroadcastTxCommand(JsonStreamMixin, BaseNetworkCommand):
    _METHOD = HttpMethod.POST
    action = "coins"
    verbose = False
    level = loading_level.LoadingLevel.NONE
    _high_priority = True

    def __init__(self, mtx: mutable_tx.MutableTransaction, parent):
        super().__init__(parent)
        self._mtx = mtx

    @property
    def args(self):
        return [self._mtx.coin.name, "tx"]

    def process_attr(self, table):
        tx_id = table["tx"]
        if tx_id != self._mtx.tx_id:
            log.error(
                f"server gives TXID: {tx_id} but sent TXID: {self._mtx.tx_id}")
        else:
            log.debug("Broadcast TX hash is fine!")
        self._mtx.send_callback(True)

    @property
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
            except Exception as e:
                raise server_error.JsonError(e)
        else:
            body = data
        self.process_attr(body)


class GetRecommendFeeCommand(ExtHostCommand):
    _BASE_URL = "https://bitcoinfees.earn.com/api/v1/fees/"
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
