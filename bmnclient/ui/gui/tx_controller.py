import logging

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot

from ...models.tx_broadcast import TransactionBroadcastModel
from ...wallet import mutable_tx

log = logging.getLogger(__name__)


class TxController(QObject):
    changeChanged = QSignal()
    canSendChanged = QSignal()
    maxAmountChanged = QSignal()
    confirmChanged = QSignal()
    changeAddressChanged = QSignal()
    sourceModelChanged = QSignal()
    useCoinBalanceChanged = QSignal()
    sent = QSignal()
    fail = QSignal(str, arguments=["error", ])
    # broadcastResult = QSignal(bool, str, arguments=["success", "error"])

    def __init__(self, parent=None, address=None):
        super().__init__(parent)
        from . import Application
        self._application = Application.instance()

        if address is None:
            self.__cm = self._application.coinManager
            self.__cm.getCoinUnspentList()
            address = self.__cm.address
        assert address
        self.__coin = address.coin
        self.__tx = mutable_tx.MutableTransaction(
            address,
            self._application.feeManager,
            self)
        self.__coin.balanceChanged.connect(self.balance_changed)
        self.__negative_change = False
        self.use_hint = True

        self._model = TransactionBroadcastModel(self._application, self.__tx)

    @QProperty(QObject, constant=True)
    def model(self) -> TransactionBroadcastModel:
        return self._model

    @QSlot()
    def balance_changed(self) -> None:
        self.maxAmountChanged.emit()
        if self.__negative_change and self.use_hint:
            if self.__tx.source_amount is not None:
                self.__tx.amount = self.__tx.source_amount
            self.__validate_change()
            self.canSendChanged.emit()
            self.confirmChanged.emit()
            self.changeChanged.emit()

    def __validate_change(self):
        self.__negative_change = self.__tx.change < 0 or self.__tx.amount <= 0. or \
            (self.__tx.subtract_fee and self.__tx.fee >= self.__tx.amount)

    @QProperty(bool, notify=changeChanged)
    def hasChange(self) -> str:
        return not self.__negative_change and self.__tx.change > 0

    @QProperty(str, notify=changeAddressChanged)
    def changeAddress(self):
        return self.__tx.leftover_address

    @QProperty('QVariantList', notify=sourceModelChanged)
    def sourceModel(self):
        return self.__tx.sources

    @QProperty(int, notify=confirmChanged)
    def confirmTime(self):
        "minutes"
        return self.__tx.estimate_confirm_time()

    @QProperty(bool, notify=canSendChanged)
    def canSend(self) -> bool:
        log.debug(
            f"amount: {self.__tx.amount} source amount:{self.__tx.source_amount } change:{self.__tx.change} fee:{self.__tx.fee}")
        if self.__tx.amount <= 0 or self.__tx.fee < 0:
            log.debug("negative amount or change")
            return False
        if self.__tx.change < 0:
            log.debug("negative change")
            return False
        if self.__tx.spb < self.__tx.MIN_SPB_FEE:
            log.debug("too low SPB")
            return False
        if self.__tx.subtract_fee and self.__tx.fee >= self.__tx.amount:
            log.debug("fee is more than amount")
            return False
        if not self.__tx.receiver_valid:
            log.debug("wrong receiver")
            return False
        if self.__tx.amount > self.__tx.source_amount:
            log.debug("amount more than balance")
            return False
        return True

    @QProperty('QVariantList', constant=True)
    def targetList(self):
        # if addr is not self.__cm.address] # why not?
        return [addr.name for addr in self.__cm.coin.wallets]

    @QProperty(bool, notify=useCoinBalanceChanged)
    def useCoinBalance(self) -> bool:
        return self.__tx.use_coin_balance

    @useCoinBalance.setter
    def _set_use_coin_balance(self, value: bool) -> None:
        if value == self.__tx.use_coin_balance:
            return
        self.__tx.use_coin_balance = value
        self.__tx.recalc_sources(True)
        self.__validate_change()
        self.useCoinBalanceChanged.emit()
        self.maxAmountChanged.emit()
        self.changeChanged.emit()
        self.sourceModelChanged.emit()
        self.canSendChanged.emit()

    @QSlot()
    def recalcSources(self):
        self.__tx.recalc_sources()
        self.maxAmountChanged.emit()
        self.canSendChanged.emit()
        self.changeChanged.emit()

    @QSlot(result=bool)
    def prepareSend(self):
        # stupid check but ..
        if not self.canSend:
            return False
        if self.__tx.amount > self.__tx.source_amount:
            return False
        try:
            self.__tx.prepare()
            self.confirmChanged.emit()
            self.changeAddressChanged.emit()
        except mutable_tx.NewTxerror as error:
            log.warning(f"cant make TX:{error}")
            self.fail.emit(str(error))
            return False
        return True

    @QSlot(result=bool)
    def send(self) -> bool:
        # stupid check but ..
        if not self.canSend:
            return False
        self.__tx.send()
        return True

    @QSlot()
    def cancel(self) -> None:
        log.debug("Cancelling TX")
        self.__tx.cancel()

    @QProperty(str, constant=True)
    def txHash(self) -> str:
        return self.__tx.tx_id or ""
