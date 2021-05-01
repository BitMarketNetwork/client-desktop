from __future__ import annotations

import logging
from typing import Iterable, List, Tuple

from . import server_error
from .. import loading_level
from ..network.api_v1.query import AbstractApiQuery
from ..wallet import address, coins, mutable_tx

log = logging.getLogger(__name__)


class AddressMultyMempoolCommand(AbstractApiQuery):
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


class MempoolMonitorCommand(AbstractApiQuery):
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


class BroadcastTxCommand(AbstractApiQuery):
    _DEFAULT_METHOD = AbstractApiQuery.Method.POST
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
