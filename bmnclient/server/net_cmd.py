from __future__ import annotations
import logging
from . import server_error
from .. import loading_level
from ..network.api_v1.query import AbstractApiQuery
from ..wallet import mutable_tx

log = logging.getLogger(__name__)


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
        if int(err_code) == 2003:
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
