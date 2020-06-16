
import enum
import io
import json
import logging
import sys
from typing import Tuple, List

import PySide2.QtCore as qt_core

from client.ui.gui import api
from client.wallet import address, coins, mtx_impl, mutable_tx, tx, key, hd

from . import server_error

log = logging.getLogger(__name__)

####################
# temporary flag due to server errors
####################
SILENCE_CHECKS = True


class AbstractNetworkCommand(qt_core.QObject):

    def __init__(self, parent):
        super().__init__(parent=parent)


class HTTPProtocol(enum.IntEnum):
    GET = enum.auto()
    POST = enum.auto()


class BaseNetworkCommand(AbstractNetworkCommand):
    action = None
    _server_action = None
    verbose = False
    host = None
    protocol = HTTPProtocol.GET

    def __init__(self, parent):
        super().__init__(parent=parent)

    @property
    def ext(self):
        return self.host is not None

    @property
    def server_action(self):
        return self._server_action or self.action

    @property
    def args(self):
        return []

    @property
    def args_get(self):
        return {}

    @property
    def post_data(self) -> bytes:
        type_, body = self._args_post()
        return json.dumps({
            "data": {
                "type": type_,
                "attributes": body,
            }
        }).encode()

    def _args_post(self) -> Tuple[str, dict]:
        """
        must be implemented for having 'post_data' working
        """
        raise NotImplementedError

    def on_data(self, data):
        if self.verbose:
            log.debug('got data: %f kB', len(data) / 1024.)
        #raise NotImplementedError()

    def on_data_end(self, http_code=200):
        raise NotImplementedError()

    def process_answer(self, data) -> AbstractNetworkCommand:
        if not data:
            raise server_error.EmptyReplyError()
        if not isinstance(data, dict):
            try:
                body = json.loads(data)
            except:
                raise server_error.JsonError()
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
        # duno what todo
        self.output(self.tr("Server error"), error.get('detail'))
        self._gcd.quit(1)

    def connect_(self, gcd):
        """
        Connect command via slot/signal connections
        """
        self._gcd = gcd

    def __str__(self):
        return self.__class__.__name__

    def drop(self):
        pass


class JsonStreamMixin:
    """
    simple collect data strategy:
    - it wastes memory and we can implement more sufficient algorithm later
    """

    def __init__(self, parent):
        super().__init__(parent)
        self._json = io.BytesIO()

    def on_data(self, data):
        super().on_data(data)
        self._json.write(data)

    def on_data_end(self, http_code):
        try:
            return self.process_answer(self._json.getvalue())
        except server_error.BaseNetError as se:
            log.error("Processing answer error: %s", se)
            HEAD_LEN = 1024
            log.error('full answer(first %d symbols): %s',
                      HEAD_LEN, self._json.getvalue()[:HEAD_LEN])

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

    def __init__(self, parent):
        super().__init__(parent)

    def process_attr(self, table):
        versions = table["version"][::-1]
        self.serverVersion.emit(*versions)
        gui_api = api.Api.get_instance()
        if gui_api:
            gui_api.uiManager.fill_coin_info_model(table["coins"])

    def connect_(self, gcd):
        super().connect_(gcd)
        self.serverVersion.connect(
            gcd.onServerVersion, qt_core.Qt.QueuedConnection)


class CoinInfoCommand(JsonStreamMixin, BaseNetworkCommand):
    action = "coins"

    def __init__(self, parent):
        super().__init__(parent=parent)

    def process_attr(self, table):
        for coin, data in table.items():
            self.output("Coin", coin)
            self.output("Active", data["status"])
            self.output("Offset", data["offset"])
            self.output("Height", data["height"])


class UpdateCoinsInfoCommand(CoinInfoCommand):
    verbose = False

    def __init__(self, poll: bool, parent):
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
            coin = self._gcd.get_coin(coin_name)
            # don't swear here. we've sworn already
            if coin is not None and coin.parse(data, self._poll, verbose=self.verbose):
                """
                important scope here
                """
                if self.verbose:
                    log.debug(f"remote {coin} changed . poll{self._poll}")
                self._gcd.saveCoin.emit(coin)
            elif self.verbose:
                log.debug(f"{coin} hasn't changed")

    def __str__(self):
        return super().__str__() + f"[poll={self._poll}]"


class AddressInfoCommand(JsonStreamMixin, BaseNetworkCommand):
    action = "coins"
    _server_action = "address"

    def __init__(self, wallet: address.CAddress, parent):
        super().__init__(parent=parent)
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


class LookForHDAddresses(AddressInfoCommand):
    """
    search all HD addresses with non zero balances
    we stop serach when ew meet unexistent address
    """
    MAX_EMPTY_NUMBER = 5

    def __init__(self, coin: coins.CoinType, parent, hd_index=0, empty_count: int = 0, segwit: bool = True, hd_: hd.HDNode = None):
        try:
            self._coin = coin
            self._hd: hd.HDNode = hd_ or coin.hd_address(hd_index)
            self._address: str = self._hd.to_address(
                key.AddressType.P2WPKH if segwit else key.AddressType.P2PKH)
            self._hd_index = hd_index
            self._empty_count = empty_count
            self._segwit = segwit
        except address.AddressError as ae:
            # TODO:
            log.error(f"error {ae}")
            self._address = None
        super().__init__(None, parent=parent)

    @property
    def args(self):
        return [self._coin.name, self._address]

    def process_attr(self, table):
        assert self._address == table["address"]
        log.debug(table)
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
    verbose = True

    def __init__(self, wallet: address.CAddress, parent):
        super().__init__(wallet, parent=parent)

    @property
    def args(self):
        return [self._wallet.coin.name, self._wallet.name]

    def process_attr(self, table):
        assert self._wallet.name == table["address"]
        #
        self._wallet.type = table["type"]
        self._wallet.tx_count = table["number_of_transactions"]
        self._wallet.balance = table["balance"]
        self._gcd.save_wallet(self._wallet)
        diff = self._wallet.tx_count - len(self._wallet.txs)
        if diff > 0 and not self._wallet.isUpdating:
            log.debug("Need to download more %s tx for %s", diff, self._wallet)
            return AddressHistoryCommand(self._wallet, parent=self)


class AddressHistoryCommand(AddressInfoCommand):
    """
    """
    action = "coins"
    _server_action = "history"

    _coin_manager = None
    verbose = False

    DEFAULT_HEIGHT = "max"
    DEFAULT_LIMIT = 50

    def __init__(self, wallet: address.CAddress,
                 limit=None,
                 tx_count=0,
                 parent=None,
                 ):
        super().__init__(wallet, parent)
        wallet.isUpdating = True
        if wallet.last_offset is None:
            self._first_offset = 'best'
            self._last_offset = wallet.first_offset
        else:
            self._first_offset = wallet.last_offset
            self._last_offset = None
        self._limit = limit
        self._tx_count = tx_count
        if self.verbose:
            log.info(
                f"WALLET  on start:{wallet} fof:{self._first_offset} lof:{self._last_offset} me:{id(self)}")
        if not self._coin_manager:
            api_inst = api.Api.get_instance()
            self._coin_manager = api_inst.coinManager if api_inst else None

    def process_attr(self, table):
        assert table.get("address") == self._wallet.name
        # log.warning(f"ADDRESS HISTORY RESULT: {table}")
        if self._first_offset == 'best':
            self._wallet.first_offset = table["first_offset"]
        last_offset = table["last_offset"]
        # use setter !!!
        self._wallet.last_offset = last_offset
        self._process_transactions(table["tx_list"])
        #  - we have to save new wallet offsets ?? .. cause app can be closed before next net calls
        self._gcd.save_wallet(self._wallet, 1000)
        if self._coin_manager:
            self._coin_manager.txModelChanged.emit()
        ###
        if last_offset is not None and \
                not self._gcd.silent_mode and \
                (self._limit is None or self.tx_count < self._limit):
            log.debug(f"Next history request for {self._wallet}")
            return self.clone()
        else:
            # self._gcd.saveAddress.emit(self._wallet)
            self._wallet.isUpdating = False

    def clone(self):
        return self.__class__(
            wallet=self._wallet,
            limit=self._limit,
            tx_count=self._tx_count
        )

    def on_data(self, data):
        # too much prints
        # super().on_data(data)
        self._json.write(data)

    @property
    def args(self):
        return [self._wallet.coin.name, self._wallet.name, self._server_action]

    @property
    def tx_count(self):
        return self._tx_count

    @property
    def args_get(self):
        get = {}
        # TODO: WTF?
        if self._first_offset is not None and self._first_offset != 'None':
            get.update({
                "first_offset": self._first_offset,
            })
        if self._limit is not None:
            if self._limit - self.tx_count < self.DEFAULT_LIMIT:
                get.update({
                    "limit": self._limit - self.tx_count,
                })
        if self._last_offset is not None:
            get.update({
                "last_offset": self._last_offset,
            })
        if self.verbose:
            log.info(f"get history opts: {get}  me:{id(self)}")
        return get

    def _process_transactions(self, txs: dict):
        for name, body in txs.items():
            # tx = coins.Transaction(self._wallet) WRONG THREAD!
            tx_ = tx.Transaction(None)
            self._tx_count += 1
            tx_.parse(name, body)
            try:
                self._wallet.add_tx(tx_)
                self._gcd.saveTx.emit(tx_)
            except tx.TxError as txe:
                if self.verbose:
                    log.warn(f"{txe}")

    def __str__(self):
        return super().__str__() + f"[wallet={self._wallet}]"


class AddressMempoolCommand(AddressInfoCommand):
    verbose = False
    _server_action = "unconfirmed"
    MAX_TIMES = 6
    WAIT_CHUNK = 100
    WAIT_TIMEOUT = 3000

    def __init__(self, wallet: address.CAddress, parent, counter=0):
        super().__init__(wallet, parent=parent)
        self._counter = counter

    @property
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
        self._process_transactions(txs)

    def _process_transactions(self, txs: dict):
        for name, body in txs.items():
            # tx = coins.Transaction(self._wallet) WRONG THREAD!
            tx_ = tx.Transaction(None)
            tx_.parse(name, body)
            try:
                self._wallet.add_tx(tx_)
                self._gcd.saveTx.emit(tx_)
            except tx.TxError as txe:
                if self.verbose:
                    log.warn(f"{txe}")


class AddressMultyMempoolCommand(JsonStreamMixin, BaseNetworkCommand):
    verbose = True
    action = "coins"
    _server_action = "unconfirmed"
    protocol = HTTPProtocol.POST
    MAX_TIMES = 6
    WAIT_CHUNK = 100
    WAIT_TIMEOUT = 3000

    def __init__(self, wallet_list: List[address.CAddress], parent, counter=0, hash_=None):
        super().__init__(parent=parent)
        assert wallet_list
        self._wallet_list = wallet_list
        self._coin = wallet_list[0].coin
        self._counter = counter
        self._hash = hash_

    @property
    def args(self):
        return [self._coin.name, self._server_action]

    def _args_post(self) -> Tuple[str, bytes]:
        table = {
            "address_list": [addr.name for addr in self._wallet_list],
        }
        if self._hash:
            table["last_hash"] = self._hash
        return self._server_action, table

    def process_attr(self, table):
        # TODO: process hash

        txs = table["tx_list"]
        self._hash = table["hash"]
        # if no TX here - then wait and check again
        if txs:
            self._process_transactions(txs)
        # sleep for a bit
        return self._send_again()

    def _process_transactions(self, txs: dict):
        for name, body in txs.items():
            log.info(body)
            inps = body["input"] + body["output"]
            tx_ = tx.Transaction(None)
            tx_.parse(name, body)
            for inp in inps:
                w = self._coin[inp["address"]]
                try:
                    w.add_tx(tx_)
                    self._gcd.saveTx.emit(tx_)
                except tx.TxError as txe:
                    if self.verbose:
                        log.warn(f"{txe}")

    def _send_again(self):
        if self.verbose:
            log.debug(f"sleep and check mempool again; {self._counter}")
        if self._counter <= self.MAX_TIMES:
            to = self.WAIT_TIMEOUT
            while to >= 0:
                to -= self.WAIT_CHUNK
                qt_core.QThread.currentThread().msleep(self.WAIT_CHUNK)
                qt_core.QCoreApplication.processEvents()
            return AddressMultyMempoolCommand(self._wallet_list, self, counter=self._counter + 1, hash_=self._hash)

    def on_data_end(self, http_code):
        if http_code == 304:
            return self._send_again()
        return super().on_data_end(http_code)


class AddressUnspentCommand(AddressInfoCommand):
    action = "coins"
    _server_action = "unspent"

    def __init__(self, wallet: address.CAddress, first_offset=None,
                 last_offset=None, unspent=None, calls: int = 0, parent=None):
        super().__init__(wallet, parent)
        self._first_offset = first_offset
        self._last_offset = last_offset
        self._unspent = unspent or []
        self._calls = calls

    @property
    def args(self):
        return [self._wallet.coin.name, self._wallet.name, self._server_action]

    @property
    def args_get(self):
        get = {}
        if self._first_offset is not None:
            get.update({
                "first_offset": self._first_offset,
            })
        if self._last_offset is not None:
            get.update({
                "last_offset": self._last_offset,
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
            self._process_transactions()

    def clone(self, first_offset):
        return self.__class__(
            wallet=self._wallet,
            unspent=self._unspent,
            first_offset=first_offset,
            calls=self._calls + 1,
        )

    def _process_transactions(self):
        # map it to separate logic layers
        if self.verbose:
            log.debug(
                f"UNSPENT COUNT: {len(self._unspent)} from {self._calls} calls")
        self._wallet.process_unspents(self._unspent)


class BroadcastTxCommand(JsonStreamMixin, BaseNetworkCommand):
    action = "coins"
    protocol = HTTPProtocol.POST
    verbose = False

    def __init__(self, mtx: mutable_tx.MutableTransaction, parent):
        super().__init__(parent)
        self._mtx = mtx

    @property
    def args(self):
        return [self._mtx.coin.name, "tx", "broadcast"]

    def process_attr(self, table):
        tx_id = table["tx"]
        if tx_id != self._mtx.tx_id:
            log.error(
                f"server gives TXID:{tx_id} but sent TXID:{self._mtx.tx_id}")
        elif self.verbose:
            log.debug("Broadcasted TX hash is fine!")
        self._mtx.send_callback(True)

    def _args_post(self):
        return ("tx_broadcast", {
            "data": str(self._mtx),
        })

    def handle_error(self, error):
        log.error(error)
        err_code = error["code"]
        if server_error.ServerErrorCode.broadcastError == err_code:
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
                raise server_error.JsonError()
        else:
            body = data
        self.process_attr(body)


class GetCoinRatesCommand(ExtHostCommand):
    """
    To retrieve coin rates
    https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd
    """
    action = "price"
    host = "https://api.coingecko.com/api/v3/simple/"
    currency = "usd"

    def __init__(self, parent=None, ):
        super().__init__(parent)

    @property
    def args_get(self):
        self._coins = self._gcd.all_enabled_coins
        coins_ = ",".join([c.basename for c in self._coins])
        return {
            "ids": coins_,
            "vs_currencies": self.currency,
        }

    def process_attr(self, table):
        for coin in self._coins:
            coin.rate = table[coin.basename][self.currency]
        # full first save here
        # self._gcd.save_coins()


class GetRecommendFeeCommand(ExtHostCommand):
    "https://bitcoinfees.earn.com/api"
    host = "https://bitcoinfees.earn.com/api/v1/fees/"
    action = "recommended"

    def process_attr(self, table):
        stats = [
            ("fastestFee", 10),
            ("halfHourFee", 30),
            ("hourFee", 60),
        ]
        self._gcd.fee_man.add_fees(
            {table[to_str]: to_int for to_str, to_int in stats})
