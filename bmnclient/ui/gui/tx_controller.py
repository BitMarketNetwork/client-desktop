

import logging

import PySide2.QtCore as qt_core

from ... import gcd
from ...wallet import key, mutable_tx, tx
from . import qml_context

log = logging.getLogger(__name__)


class TxController(qt_core.QObject):
    amountChanged = qt_core.Signal()
    feeChanged = qt_core.Signal()
    changeChanged = qt_core.Signal()
    canSendChanged = qt_core.Signal()
    substractChanged = qt_core.Signal()
    newAddressForLeftoverChanged = qt_core.Signal()
    receiverChanged = qt_core.Signal()
    maxAmountChanged = qt_core.Signal()
    confirmChanged = qt_core.Signal()
    changeAddressChanged = qt_core.Signal()
    sourceModelChanged = qt_core.Signal()
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
            self.__cm = qml_context.BackendContext.get_instance().coinManager
            self.__cm.getCoinUnspentList()
            address = self.__cm.address
        assert address
        self.__coin = address.coin
        self.__tx = mutable_tx.MutableTransaction(
            address,
            gcd.GCD.get_instance().fee_man,
            self
        )
        # we should keep it avoiding rounding issues when user input amount manually
        self.__human_amount = self.__round(self.__tx.amount)
        # while we can send only from one address then we show max amount from this address only
        self.__spb_factor: float = None  # recommended value
        self.spbFactor = 0.5
        # update UTXO right now
        self.__coin.balanceChanged.connect(self.balance_changed)
        # do we need make it too often ?
        # qt_core.QTimer.singleShot(1000, self.recalcSources)
        self.__negative_change = False
        self.use_hint = True

    @qt_core.Slot()
    def balance_changed(self):
        self.maxAmountChanged.emit()
        if self.__negative_change and self.use_hint:
            self.__update_amount(self.__tx.source_amount)
        # api.Api.get_instance().show_spinner(False)

    def __round(self, value: float, fiat: bool = False) -> str:
        if fiat:
            return str(self.__coin.fiat_amount(value))
        return str(self.__coin.balance_human(value))

    def __parse(self, value: str) -> float:
        return self.__coin.from_human(value)

    @qt_core.Property(str, notify=maxAmountChanged)
    def maxAmount(self):
        return self.__round(self.__tx.source_amount)

    @qt_core.Property(str, notify=amountChanged)
    def filteredAmount(self):
        "minimum amount to cover amount"
        return self.__round(self.__tx.filtered_amount)

    @qt_core.Property(str, notify=amountChanged)
    def amount(self):
        return self.__human_amount

    @amount.setter
    def _set_amount(self, value: str) -> None:
        self.__human_amount = value
        self.__tx.amount = int(self.__parse(value))
        self.__update_amount()

    def __update_amount(self, amount=None):
        if amount is not None:
            self.__tx.amount = amount
        human_amount = self.__round(self.__tx.amount)
        if self.__tx.amount != int(self.__parse(self.__human_amount)):
            self.__human_amount = human_amount
        self.__validate_change()
        # log.debug( f"AMOUNT human:{self.__human_amount} real:{self.__tx.amount}")
        self.amountChanged.emit()
        self.canSendChanged.emit()
        self.confirmChanged.emit()
        self.changeChanged.emit()

    @qt_core.Property(bool, notify=newAddressForLeftoverChanged)
    def newAddressForChange(self):
        return self.__tx.new_address_for_change

    @newAddressForChange.setter
    def set_new_address_for_leftover(self, on):
        if on == self.__tx.new_address_for_change:
            return
        log.debug(f"use new address for change: {on}")
        self.__tx.new_address_for_change = on
        self.newAddressForLeftoverChanged.emit()

    @qt_core.Property(bool, notify=substractChanged)
    def substractFee(self):
        return self.__tx.substract_fee

    @substractFee.setter
    def set_substract_fee(self, on):
        if on == self.__tx.substract_fee:
            return
        log.debug(f" substract fee: {on}")
        self.__tx.substract_fee = on
        self.__validate_change()
        self.substractChanged.emit()
        self.changeChanged.emit()
        self.canSendChanged.emit()

    @qt_core.Property(str, notify=amountChanged)
    def fiatAmount(self):
        return self.__round(self.__tx.amount, True)

    @qt_core.Property(str, notify=maxAmountChanged)
    def fiatBalance(self):
        return self.__round(self.__tx.source_amount, True)

    @qt_core.Property(str, notify=feeChanged)
    def spbAmount(self):
        return str(self.__tx.spb)

    @spbAmount.setter
    def _set_spb_amount(self, value: str):
        log.debug(value)
        if value == str(self.__tx.spb):
            return
        self.__tx.spb = int(value)
        self.feeChanged.emit()
        self.changeChanged.emit()
        self.confirmChanged.emit()
        self.canSendChanged.emit()

    @qt_core.Property(str, notify=feeChanged)
    def feeAmount(self):
        return self.__round(self.__tx.fee)

    @qt_core.Property(str, notify=feeChanged)
    def feeFiatAmount(self):
        return self.__round(self.__tx.fee, True)

    @qt_core.Property(float, notify=feeChanged)
    def spbFactor(self) -> float:
        return self.__spb_factor

    @spbFactor.setter
    def _set_spb_factor(self, value: float) -> None:
        assert isinstance(value, (float, int))
        assert value >= 0. and value <= 1.
        if self.__spb_factor == value:
            return
        self.__spb_factor = value
        self.__tx.spb = (value * (self.__tx.MAX_SPB_FEE -
                                  self.__tx.MIN_SPB_FEE)) + self.__tx.MIN_SPB_FEE
        self.__validate_change()
        self.feeChanged.emit()
        self.changeChanged.emit()
        self.confirmChanged.emit()
        self.canSendChanged.emit()

    @qt_core.Property(str, notify=changeChanged)
    def changeAmount(self):
        return self.__round(max(0, self.__tx.change))

    def __validate_change(self):
        self.__negative_change = self.__tx.change < 0 or self.__tx.amount <= 0. or \
            (self.__tx.substract_fee and self.__tx.fee >= self.__tx.amount)

    @qt_core.Property(bool, notify=changeChanged)
    def hasChange(self) -> str:
        return not self.__negative_change and self.__tx.change > 0

    @qt_core.Property(bool, notify=changeChanged)
    def wrongAmount(self):
        return self.__negative_change

    @qt_core.Property(str, notify=changeAddressChanged)
    def changeAddress(self):
        return self.__tx.leftover_address

    @qt_core.Property('QVariantList', notify=sourceModelChanged)
    def sourceModel(self):
        return self.__tx.sources

    @qt_core.Property(str, notify=receiverChanged)
    def receiverAddress(self):
        return self.__tx.receiver

    @qt_core.Property(bool, notify=receiverChanged)
    def receiverValid(self):
        return self.__tx.receiver_valid

    @receiverAddress.setter
    def _set_receiver(self, address: str):
        self.__tx.receiver = address
        self.receiverChanged.emit()
        self.canSendChanged.emit()

    @qt_core.Property(int, notify=confirmChanged)
    def confirmTime(self):
        "minutes"
        return self.__tx.estimate_confirm_time()

    @qt_core.Property(bool, notify=canSendChanged)
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
        if self.__tx.substract_fee and self.__tx.fee >= self.__tx.amount:
            log.debug("fee is more than amount")
            return False
        if not self.__tx.receiver_valid:
            log.debug("wrong receiver")
            return False
        if self.__tx.amount > self.__tx.source_amount:
            log.debug("amount more than balance")
            return False
        return True

    @qt_core.Property('QVariantList', constant=True)
    def targetList(self):
        # if addr is not self.__cm.address] # why not?
        return [addr.name for addr in self.__cm.coin.wallets]

    @qt_core.Property(bool, notify=useCoinBalanceChanged)
    def useCoinBalance(self) -> bool:
        return self.__tx.use_coin_balance

    @useCoinBalance.setter
    def _set_use_coin_balance(self, value: bool) -> None:
        if value == self.__tx.use_coin_balance:
            return
        self.__tx.use_coin_balance = value
        self.__tx.recalc_sources(True)
        self.__validate_change()
        if self.__negative_change:
            self.setMax()
        self.useCoinBalanceChanged.emit()
        self.maxAmountChanged.emit()
        self.changeChanged.emit()
        self.feeChanged.emit()
        self.sourceModelChanged.emit()
        self.canSendChanged.emit()

    @qt_core.Slot()
    def less(self):
        #TODO: later
        log.debug("amount less")

    @qt_core.Slot()
    def more(self):
        #TODO: later
        log.debug("amount more")

    @qt_core.Slot()
    def recalcSources(self):
        self.__tx.recalc_sources()
        self.maxAmountChanged.emit()
        self.canSendChanged.emit()
        self.changeChanged.emit()

    @qt_core.Slot()
    def setMax(self):
        self.__tx.set_max()
        self.__update_amount()

    @qt_core.Slot(result=bool)
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

    @qt_core.Slot(result=bool)
    def send(self) -> bool:
        # stupid check but ..
        if not self.canSend:
            return False
        self.__tx.send()
        return True

    @qt_core.Slot()
    def cancel(self) -> None:
        log.debug("Cancelling TX")
        self.__tx.cancel()

    @qt_core.Property(str, constant=True)
    def txHash(self) -> str:
        return self.__tx.tx_id or ""

    # for tests
    @property
    def impl(self):
        return self.__tx
