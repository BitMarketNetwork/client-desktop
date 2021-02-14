import logging
from threading import Lock

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot

from ...models.tx_broadcast import \
    TransactionBroadcastAmountModel, \
    TransactionBroadcastAvailableAmountModel, \
    TransactionBroadcastChangeAmountModel, \
    TransactionBroadcastFeeAmountModel, \
    TransactionBroadcastReceiverModel
from ...wallet import mutable_tx

log = logging.getLogger(__name__)


class TxController(QObject):
    changeChanged = QSignal()
    canSendChanged = QSignal()
    newAddressForLeftoverChanged = QSignal()
    maxAmountChanged = QSignal()
    confirmChanged = QSignal()
    changeAddressChanged = QSignal()
    sourceModelChanged = QSignal()
    useCoinBalanceChanged = QSignal()
    #
    sent = QSignal()
    fail = QSignal(str, arguments=["error", ])
    # broadcastResult = QSignal(bool, str, arguments=["success", "error"])

    def __init__(self, parent=None, address=None):
        super().__init__(parent)
        if address is None:
            from . import Application
            self.__cm = Application.instance().coinManager
            self.__cm.getCoinUnspentList()
            address = self.__cm.address
        assert address
        self.__coin = address.coin
        from . import Application
        self.__tx = mutable_tx.MutableTransaction(
            address,
            Application.instance().feeManager,
            self
        )
        # while we can send only from one address then we show max amount from this address only
        # update UTXO right now
        self.__coin.balanceChanged.connect(self.balance_changed)
        # do we need make it too often ?
        # qt_core.QTimer.singleShot(1000, self.recalcSources)
        self.__negative_change = False
        self.use_hint = True

        from . import Application
        self._application = Application.instance()
        self._refresh_lock = Lock()

        self._available_amount_model = TransactionBroadcastAvailableAmountModel(
            self._application,
            self.__tx)
        self._available_amount_model.stateChanged.connect(
            lambda: self.refresh(self._available_amount_model))

        self._amount_model = TransactionBroadcastAmountModel(
            self._application,
            self.__tx)
        self._amount_model.stateChanged.connect(
            lambda: self.refresh(self._amount_model))

        self._fee_amount_model = TransactionBroadcastFeeAmountModel(
            self._application,
            self.__tx)
        self._fee_amount_model.stateChanged.connect(
            lambda: self.refresh(self._fee_amount_model))

        self._change_amount_model = TransactionBroadcastChangeAmountModel(
            self._application,
            self.__tx)
        self._change_amount_model.stateChanged.connect(
            lambda: self.refresh(self._change_amount_model))

        self._receiver_model = TransactionBroadcastReceiverModel(
            self._application,
            self.__tx)
        self._receiver_model.stateChanged.connect(
            lambda: self.refresh(self._receiver_model))

    @QProperty(TransactionBroadcastAvailableAmountModel, constant=True)
    def availableAmount(self) -> TransactionBroadcastAvailableAmountModel:
        return self._available_amount_model

    @QProperty(TransactionBroadcastAmountModel, constant=True)
    def amount(self) -> TransactionBroadcastAmountModel:
        return self._amount_model

    @QProperty(TransactionBroadcastFeeAmountModel, constant=True)
    def feeAmount(self) -> TransactionBroadcastFeeAmountModel:
        return self._fee_amount_model

    @QProperty(TransactionBroadcastChangeAmountModel, constant=True)
    def changeAmount(self) -> TransactionBroadcastChangeAmountModel:
        return self._change_amount_model

    @QProperty(TransactionBroadcastReceiverModel, constant=True)
    def receiver(self) -> TransactionBroadcastReceiverModel:
        return self._receiver_model

    def refresh(self, initiator: object) -> None:
        if self._refresh_lock.acquire(False):
            for a in dir(self):
                if a.startswith("_") and a.endswith("_model"):
                    a = getattr(self, a)
                    if initiator is not a and hasattr(a, "refresh"):
                        a.refresh()
            self.__validate_change()
            self._refresh_lock.release()


    @QSlot()
    def balance_changed(self):
        self.maxAmountChanged.emit()
        if self.__negative_change and self.use_hint:
            if self.__tx.source_amount is not None:
                self.__tx.amount = self.__tx.source_amount
            self.__validate_change()
            self.canSendChanged.emit()
            self.confirmChanged.emit()
            self.changeChanged.emit()

    @QProperty(bool, notify=newAddressForLeftoverChanged)
    def newAddressForChange(self):
        return self.__tx.new_address_for_change

    @newAddressForChange.setter
    def set_new_address_for_leftover(self, on):
        if on == self.__tx.new_address_for_change:
            return
        log.debug(f"use new address for change: {on}")
        self.__tx.new_address_for_change = on
        self.newAddressForLeftoverChanged.emit()

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
