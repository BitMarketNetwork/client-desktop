from __future__ import annotations

import json
import logging
from typing import Iterable, List, Optional, Tuple

from . import server_error
from .. import loading_level
from ..network.api_v1.query import AbstractServerApiQuery
from ..wallet import address, coins, mutable_tx

log = logging.getLogger(__name__)


class AbstractQuery(AbstractServerApiQuery):
    action = None
    _server_action = None
    level = loading_level.LoadingLevel.NONE
    unique = False

    def __init__(self, parent=None, **kwargs) -> None:
        super().__init__()
        self.level = kwargs.pop("level", loading_level.LoadingLevel.NONE)
        assert not kwargs

    @property
    def ext(self) -> bool:
        return self._DEFAULT_BASE_URL is not None

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

    def process_attr(self, table):
        pass


class AddressInfoCommand(AbstractQuery):
    action = "coins"
    _server_action = "address"
    level = loading_level.LoadingLevel.ADDRESSES

    def __init__(self, wallet: address.CAddress, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self._address = wallet

    @property
    def args(self):
        return [self._address.coin.name, self._address.name]


class LookForHDAddresses(AddressInfoCommand):
    """
    search all HD addresses with non zero balances
    we stop search when ew meet unexistent address
    """
    MAX_EMPTY_NUMBER = 6
    level = loading_level.LoadingLevel.ADDRESSES

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
            wallet = address.CAddress(self._coin, name=self._address)
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
    level = loading_level.LoadingLevel.TRANSACTIONS

    def __init__(self, wallet: address.CAddress, parent=None, **kwargs):
        super().__init__(wallet, parent=parent, **kwargs)

    @property
    def args(self):
        return [self._address.coin.name, self._address.name]

    def process_attr(self, table):
        assert self._address.name == table["address"]
        log.warning(table)
        # type important!! do not remove
        type_ = table["type"]
        txCount = table["number_of_transactions"]
        balance = table["balance"]
        if balance != self._address.amount or \
                txCount != self._address.txCount or \
                type_ != self._address.type:
            self._address.type = type_
            self._address.amount = balance
            #self._address.txCount = txCount
            from ..application import CoreApplication
            CoreApplication.instance().databaseThread.save_address(self._address)
            diff = txCount - self._address.realTxCount
            if diff > 0 and not self._address.is_going_update:
                log.debug("Need to download more %s tx for %s",
                          diff, self._address)
                return AddressHistoryCommand(self._address, parent=self)


class AddressHistoryCommand(AddressInfoCommand):
    action = "coins"
    _server_action = "history"
    level = loading_level.LoadingLevel.TRANSACTIONS

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
        log.debug(
            f"request: FORTH:{self.__forth} first off:{self.__first_offset} last off:{self.__last_offset}")

    def process_attr(self, table):
        assert table.get("address") == self._address.name
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
        log.info(f"get history opts: {get}  me:{id(self)}")
        return get

    def __process_transactions(self, txs: dict):
        tx_list = ServerTxParser().parseList(txs, self._address)
        if tx_list:
            from ..application import CoreApplication
            db = CoreApplication.instance().databaseThread.database
            for tx in tx_list:
                db._write_transaction(tx)

        # raw count
        self.__tx_count += len(tx_list)
        for tx in tx_list:
            if self.__forth and self.__first_offset == 'best':
                from ..ui.gui import Application
                Application.instance().uiManager.process_incoming_tx(tx)

    @property
    def skip(self) -> bool:
        return self._address.deleted

    def __str__(self):
        return f"<{super().__str__()}> [wallet={self._address} foff:{self.__first_offset}]"


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
            "address_list": [a.name for a in self._wallet_list],
        }
        if self._hash:
            table["last_hash"] = self._hash
        return self._server_action, table


class AddressMultyMempoolCommand(AbstractMultyMempoolCommand):
    MAX_TIMES = 5
    WAIT_CHUNK = 100
    WAIT_TIMEOUT = 3000

    def __init__(self, wallet_list: List[address.CAddress], parent, counter=0, hash_=None):
        super().__init__(wallet_list=wallet_list, parent=parent, hash_=hash_)
        self.__counter = counter
        self._coin = wallet_list[0].coin

    def process_attr(self, table):
        log.warning(table)

        txs = table["tx_list"]
        self._hash = table["hash"]
        if txs:
            self.__counter += 1
            self.__process_transactions(txs)
        self.__send_again()

    def __process_transactions(self, txs: dict):
        for name, body in txs.items():
            log.debug(body)
            self.__process_transaction(name, body)

    def __process_transaction(self, name: str, body: dict) -> None:
        for inp in body["input"] + body["output"]:
            w = self._coin[inp["address"]]
            if w is not None:
                tx = TxParser(TxParser.ParseFlag.MEMPOOL).parse(
                    name,
                    body,
                    w)
                if tx:
                    from ..ui.gui import Application
                    Application.instance().uiManager.process_incoming_tx(tx)

    def __send_again(self):
        log.debug(f"sleep and check mempool again; {self.__counter}")
        if self.__counter <= self.MAX_TIMES:
            #to = self.WAIT_TIMEOUT
            #while to >= 0:
            #    to -= self.WAIT_CHUNK
            #    qt_core.QThread.currentThread().msleep(self.WAIT_CHUNK)
            #    qt_core.QCoreApplication.processEvents()

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
    def __init__(self, coin: coins.CoinType, parent, hash_=None):
        super().__init__(wallet_list=iter(coin.addressList), parent=parent, hash_=hash_)
        self._coin = coin

    def onResponseFinished(self) -> None:
        if self.statusCode != 304:
            super().onResponseFinished()

    def process_attr(self, table):
        log.warning(table)
        self._hash = table["hash"]
        for name, body in table["tx_list"].items():
            log.debug(body)
            self.__process_transaction(name, body)

    def __process_transaction(self, name: str, body: dict) -> None:
        for inp in body["input"] + body["output"]:
            w = self._coin[inp["address"]]
            if w is not None:
                tx = TxParser(TxParser.ParseFlag.MEMPOOL).parse(
                    name,
                    body,
                    w)
                if tx:
                    from ..ui.gui import Application
                    Application.instance().uiManager.process_incoming_tx(tx)


class AddressUnspentCommand(AddressInfoCommand):
    action = "coins"
    _server_action = "unspent"
    level = loading_level.LoadingLevel.NONE

    def __init__(self, wallet: address.CAddress, first_offset=None,
                 last_offset=None, unspent=None, calls: int = 0, parent=None):
        super().__init__(wallet, parent)
        self._first_offset = first_offset
        self._last_offset = last_offset
        self._unspent = unspent or []
        self._calls = calls

    @property
    def args(self):
        return [self._address.coin.name, self._address.name, self._server_action]

    def createRequestData(self) -> Optional[dict]:
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
        assert table.get("address") == self._address.name
        last_offset = table["last_offset"]
        log.debug("TX IN ANSWER %d ,%s", len(table["tx_list"]), self)
        self._unspent += table["tx_list"]
        if last_offset is not None:
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
        log.debug(
            f"UNSPENT COUNT: {len(self._unspent)} from {self._calls} calls")
        self._address.process_unspents(self._unspent)
        self._address.coin.model._tx_controller.recalcSources()  # TODO


class BroadcastTxCommand(AbstractQuery):
    _DEFAULT_METHOD = AbstractQuery.Method.POST
    action = "coins"
    level = loading_level.LoadingLevel.NONE

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
            #raise server_error.EmptyReplyError()
            return

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
