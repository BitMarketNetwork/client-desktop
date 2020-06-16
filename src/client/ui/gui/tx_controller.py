

import logging

import PySide2.QtCore as qt_core

from client import gcd

from ...wallet import key, mutable_tx, tx
from . import api, coin_manager

log = logging.getLogger(__name__)


class TxController(qt_core.QObject):
    amountChanged = qt_core.Signal()
    feeChanged = qt_core.Signal()
    changeChanged = qt_core.Signal()
    balanceChanged = qt_core.Signal()
    canSendChanged = qt_core.Signal()
    substractChanged = qt_core.Signal()
    newAddressForLeftoverChanged = qt_core.Signal()
    receiverChanged = qt_core.Signal()
    maxAmountChanged = qt_core.Signal()
    confirmChanged = qt_core.Signal()
    changeAddressChanged = qt_core.Signal()
    useCoinBalanceChanged = qt_core.Signal()
    #
    sent = qt_core.Signal()
    fail = qt_core.Signal(str, arguments=["error", ])
    # broadcastResult = qt_core.Signal(bool, str, arguments=["success", "error"])
    """
    """

    def __init__(self, parent=None, address=None):
        super().__init__(parent)
        if address is None:
            self._cm = api.Api.get_instance().coinManager
            self._cm.getCoinUnspentList()
            address = self._cm.address
        assert address
        self._coin = address.coin
        self._tx = mutable_tx.MutableTransaction(
            address,
            gcd.GCD.get_instance().fee_man,
            self
        )
        # we should keep it avoiding rounding issues when user input amount manually
        self._human_amount = self._round(self._tx.amount)
        # while we can send only from one address then we show max amount from this address only
        self._spb_factor: float = None  # recommended value
        self.spbFactor = 0.5
        # update UTXO right now
        self._coin.balanceChanged.connect(self.balance_changed)
        # do we need make it too often ?
        # qt_core.QTimer.singleShot(1000, self.recalcSources)
        self._negative_change = True

    @qt_core.Slot()
    def balance_changed(self):
        self.balanceChanged.emit()
        self._update_amount(self._tx.source_amount)
        api.Api.get_instance().show_spinner(False)

    def _round(self, value: float, fiat: bool = False) -> str:
        if fiat:
            return str(self._coin.fiat_amount(value))
        return str(self._coin.balance_human(value))

    def _parse(self, value: str) -> float:
        return self._coin.from_human(value)

    @qt_core.Property(str, notify=maxAmountChanged)
    def maxAmount(self):
        return self._round(self._tx.source_amount)

    @qt_core.Property(str, notify=amountChanged)
    def amount(self):
        return self._human_amount

    @amount.setter
    def _set_amount(self, value: str) -> None:
        self._human_amount = value
        self._tx.amount = int(self._parse(value))
        self._update_amount()

    def _update_amount(self, amount = None):
        if amount is not None:
            # self._tx.guess_amount()
            self._tx.amount = amount
        self._human_amount = self._round(self._tx.amount)
        self.amountChanged.emit()
        self.canSendChanged.emit()
        self.confirmChanged.emit()
        self.changeChanged.emit()

    @qt_core.Property(bool, notify=newAddressForLeftoverChanged)
    def newAddressForChange(self):
        return self._tx.new_address_for_change

    @newAddressForChange.setter
    def set_new_address_for_leftover(self, on):
        if on == self._tx.new_address_for_change:
            return
        log.debug(f"use new address for change: {on}")
        self._tx.new_address_for_change = on
        self.newAddressForLeftoverChanged.emit()

    @qt_core.Property(bool, notify=substractChanged)
    def substractFee(self):
        return self._tx.substract_fee

    @substractFee.setter
    def set_substract_fee(self, on):
        if on == self._tx.substract_fee:
            return
        log.debug(f" substract fee: {on}")
        self._tx.substract_fee = on
        self.substractChanged.emit()
        self.changeChanged.emit()
        self.canSendChanged.emit()

    @qt_core.Property(str, notify=amountChanged)
    def fiatAmount(self):
        return self._round(self._tx.amount, True)

    @qt_core.Property(str, notify=balanceChanged)
    def fiatBalance(self):
        return self._round(self._tx.source_amount, True)

    @qt_core.Property(str, notify=feeChanged)
    def spbAmount(self):
        return str(self._tx.spb)

    @spbAmount.setter
    def _set_spb_amount(self, value: str):
        log.debug(value)
        if value == str(self._tx.spb):
            return
        self._tx.spb = int(value)
        self.feeChanged.emit()
        self.changeChanged.emit()
        self.confirmChanged.emit()
        self.canSendChanged.emit()

    @qt_core.Property(str, notify=feeChanged)
    def feeAmount(self):
        return self._round(self._tx.fee)

    @qt_core.Property(str, notify=feeChanged)
    def feeFiatAmount(self):
        return self._round(self._tx.fee, True)

    @qt_core.Property(float, notify=feeChanged)
    def spbFactor(self) -> float:
        return self._spb_factor

    @spbFactor.setter
    def _set_spb_factor(self, value: float) -> None:
        assert isinstance(value, (float, int))
        assert value >= 0. and value <= 1.
        if self._spb_factor == value:
            return
        self._spb_factor = value
        self._tx.spb = (value * (self._tx.MAX_SPB_FEE -
                                 self._tx.MIN_SPB_FEE)) + self._tx.MIN_SPB_FEE
        self.feeChanged.emit()
        self.changeChanged.emit()
        self.confirmChanged.emit()
        self.canSendChanged.emit()

    @qt_core.Property(str, notify=changeChanged)
    def changeAmount(self):
        change = self._tx.change
        self._negative_change = change < 0 or self._tx.amount == 0.
        return self._round(max(0, change))

    @qt_core.Property(bool, notify=changeChanged)
    def wrongAmount(self):
        return self._negative_change

    @qt_core.Property(str, notify=changeAddressChanged)
    def changeAddress(self):
        return self._tx.leftover_address

    @qt_core.Property('QVariantList', constant=True)
    def sourceModel(self):
        return self._tx.sources

    @qt_core.Property(str, notify=receiverChanged)
    def receiverAddress(self):
        return self._tx.receiver

    @qt_core.Property(bool, notify=receiverChanged)
    def receiverValid(self):
        return self._tx.receiver_valid

    @receiverAddress.setter
    def _set_receiver(self, address: str):
        self._tx.receiver = address
        self.receiverChanged.emit()
        self.canSendChanged.emit()

    @qt_core.Property(int, notify=confirmChanged)
    def confirmTime(self):
        "minutes"
        return self._tx.estimate_confirm_time()

    @qt_core.Property(bool, notify=canSendChanged)
    def canSend(self):
        log.debug(
            f"amount: {self._tx.amount} source amount:{self._tx.source_amount } change:{self._tx.change}")
        if self._tx.amount <= 0 or self._tx.fee < 0:
            log.debug("negative amounts")
            return False
        if self._tx.change < 0:
            log.debug("negative change")
            return False
        if self._tx.spb < self._tx.MIN_SPB_FEE:
            log.debug("too low SPB")
            return False
        if not self._tx.receiver_valid:
            log.debug("wrong receiver")
            return False
        if self._tx.amount > self._tx.source_amount:
            log.debug("amount more than balance")
            return False
        return True

    @qt_core.Property('QVariantList', constant=True)
    def targetList(self):
        # if addr is not self._cm.address] # why not?
        return [addr.name for addr in self._cm.coin.wallets]

    @qt_core.Property(bool, notify=useCoinBalanceChanged)
    def useCoinBalance(self) -> bool:
        return self._tx.use_coin_balance

    @useCoinBalance.setter
    def _set_use_coin_balance(self, value: bool) -> None:
        if value == self._tx.use_coin_balance:
            return
        self._tx.use_coin_balance = value
        self.useCoinBalanceChanged.emit()
        self.maxAmountChanged.emit()
        self.changeChanged.emit()
        self.feeChanged.emit()
        self.canSendChanged

    @qt_core.Slot()
    def less(self):
        log.debug("amount less")

    @qt_core.Slot()
    def more(self):
        log.debug("amount more")

    @qt_core.Slot()
    def recalcSources(self):
        self._tx.recalc_sources()
        self._tx.guess_amount()
        self.maxAmountChanged.emit()
        self.canSendChanged.emit()
        self.changeChanged.emit()

    @qt_core.Slot()
    def setMax(self):
        self._update_amount(self._tx.source_amount -
                            (0 if self._tx.substract_fee else self._tx.fee))

    # actions

    @qt_core.Slot(result=bool)
    def prepareSend(self):
        # stupid check but ..
        if not self.canSend:
            return False
        if self._tx.amount > self._tx.source_amount:
            return False
        try:
            self._tx.prepare()
            self.confirmChanged.emit()
            self.changeAddressChanged.emit()
        except mutable_tx.NewTxerror as error:
            log.warn(f"cant make TX:{error}")
            self.fail.emit(str(error))
            return False
        return True

    @qt_core.Slot(result=bool)
    def send(self) -> bool:
        # self._recalc_timer.stop()
        # stupid check but ..
        if not self.canSend:
            return False
        self._tx.send()

        # NO !!!!!!!!!
        # self.sent.emit()

        return True

    @qt_core.Slot()
    def cancel(self) -> None:
        log.debug("Cancelling TX")
        self._tx.cancel()

    @qt_core.Property(str, constant=True)
    def txHash(self) -> str:
        return self._tx.tx_id or ""
