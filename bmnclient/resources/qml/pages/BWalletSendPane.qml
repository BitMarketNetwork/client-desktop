import Bmn 1.0
import "../application"
import "../basiccontrols"
import "../coincontrols"
import "../dialogs"

BPane {
    id: _base
    property string title: qsTr("Send")
    property BCoinObject coin: null

    contentItem: BScrollView {
        id: _scrollView
        BControl {
            width: _scrollView.viewWidth
            height: _scrollView.viewHeight
            padding: _applicationStyle.padding

            contentItem: BDialogLayout {
                columns: 3

                BDialogPromtLabel {
                    text: qsTr("Coin:")
                }
                BDialogInputLabel {
                    BLayout.columnSpan: 2
                    text: _base.coin.name
                }

                BDialogSeparator {}

                BDialogPromtLabel {
                    text: qsTr("Send to:")
                }
                BDialogInputTextField {
                    id: _receiverAddress
                    onTextChanged: {
                        _tx_controller.receiverAddress = text
                    }
                }
                BDialogValidLabel {
                    mode: {
                        if (_receiverAddress.text.length > 0) {
                            return _tx_controller.receiverValid
                                    ? BDialogValidLabel.Mode.Accept
                                    : BDialogValidLabel.Mode.Reject
                        } else {
                            return BDialogValidLabel.Mode.Unset
                        }
                    }
                }

                BDialogPromtLabel {
                    text: qsTr("Available amount:")
                }
                BAmountLabel {
                    BLayout.columnSpan: 2
                    BLayout.alignment: _applicationStyle.dialogInputAlignment
                    orientation: Qt.Horizontal
                    amount.valueHuman: _tx_controller.maxAmount
                    amount.unit: BBackend.coinManager.unit
                    amount.fiatValueHuman: _tx_controller.fiatBalance
                    amount.fiatUnit: BBackend.coinManager.currency
                }

                BDialogPromtLabel {
                    text: qsTr("Amount:")
                }
                BAmountInput {
                    id: _amount
                    BLayout.alignment: _applicationStyle.dialogInputAlignment
                    orientation: Qt.Horizontal
                    amount.valueHuman: _tx_controller.amount
                    amount.unit: BBackend.coinManager.coin.unit
                    amount.fiatValueHuman: _tx_controller.fiatAmount
                    amount.fiatUnit: BBackend.coinManager.currency

                    onSetMaxValue: {
                        _tx_controller.setMax()
                    }
                    onValueEdited: {
                        _tx_controller.amount = value
                    }
                    onFiatValueEdited: {
                        // TODO
                    }
                }
                BDialogValidLabel {
                    mode: {
                        if (_amount.value.length > 0) {
                            return !_tx_controller.wrongAmount
                                ? BDialogValidLabel.Mode.Accept
                                : BDialogValidLabel.Mode.Reject
                        } else {
                            return BDialogValidLabel.Mode.Unset
                        }
                    }
                }

                BDialogSeparator {}

                BDialogPromtLabel {
                    text: qsTr("Substract fee from amount:")
                }
                BDialogInputSwitch {
                    BLayout.columnSpan: 2
                    checked: _tx_controller.substractFee
                    onCheckedChanged: {
                        _tx_controller.substractFee = checked
                    }
                }

                BDialogPromtLabel {
                    text: qsTr("Fee:")
                }
                BAmountLabel {
                    BLayout.columnSpan: 2
                    BLayout.alignment: _applicationStyle.dialogInputAlignment
                    orientation: Qt.Horizontal
                    amount.valueHuman: _tx_controller.feeAmount
                    amount.unit: BBackend.coinManager.unit
                    amount.fiatValueHuman: "-" // TODO
                    amount.fiatUnit: BBackend.coinManager.currency
                }

                BDialogPromtLabel {}
                BFeeInput {
                    BLayout.columnSpan: 2
                    BLayout.alignment: _applicationStyle.dialogInputAlignment

                    feeFactor: _tx_controller.spbFactor
                    onFeeFactorChanged: {
                        _tx_controller.spbFactor = feeFactor
                    }

                    feeAmount: _tx_controller.spbAmount
                    onFeeAmountChanged: {
                        _tx_controller.spbAmount = feeAmount
                    }

                    confirmTime: _tx_controller.confirmTime
                }

                BDialogSeparator {}

                BDialogPromtLabel {
                    text: qsTr("Change:")
                }
                BAmountLabel {
                    BLayout.columnSpan: 2
                    BLayout.alignment: _applicationStyle.dialogInputAlignment
                    orientation: Qt.Horizontal
                    amount.valueHuman: _tx_controller.changeAmount
                    amount.unit: BBackend.coinManager.unit
                    amount.fiatValueHuman: "-" // TODO
                    amount.fiatUnit: BBackend.coinManager.currency
                }

                BDialogPromtLabel {
                    text: qsTr("Send change to new address:")
                }
                BDialogInputSwitch {
                    BLayout.columnSpan: 2
                    checked: _tx_controller.newAddressForChange
                    onCheckedChanged: {
                        _tx_controller.newAddressForChange = checked
                    }
                }

                BDialogSeparator {}

                BDialogPromtLabel {
                    text: qsTr("Source inputs:")
                }
                BAddressSourceBox {
                    model: _tx_controller.sourceModel
                    onChanged: {
                        _tx_controller.recalcSources()
                    }
                }

                BDialogInputButtonBox {
                    BButton {
                        id: _acceptButton
                        BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
                        text: qsTr("Prepare...")
                        enabled: _tx_controller.canSend
                    }
                    BButton {
                        BDialogButtonBox.buttonRole: BDialogButtonBox.ResetRole
                        text: BStandardText.buttonText.resetRole
                    }
                    onReset: {
                    }
                    onAccepted: {
                        if (_tx_controller.prepareSend()) {
                            _approveDialog.type = BTxApproveDialog.Type.Prepare
                            _approveDialog.txText = ""
                            _approveDialog.open()
                        }
                    }
                }
                BDialogSpacer {}
            }
        }
    }

    TxController {
        id: _tx_controller

        useCoinBalance: true // TODO temporary fix

        onFail: {
            console.error(error)
            _applicationManager.messageDialog(error)
        }
        onSent: {
            _approveDialog.type = BTxApproveDialog.Type.Final
            _approveDialog.txText = txHash
            _approveDialog.open()
        }

        function less() {}
        function more() {}
    }

    BTxApproveDialog {
        id: _approveDialog
        type: BTxApproveDialog.Type.Final
        coin: _base.coin // TODO BBackend.coinManager.coin.netName ???

        targetAddressText: _tx_controller.receiverAddress
        changeAddressText: _tx_controller.changeAddress

        amount.valueHuman: _tx_controller.amount
        amount.unit: BBackend.coinManager.unit
        // TODO amount.fiatValueHuman
        // TODO amount.fiatUnit:
        feeAmount.valueHuman: _tx_controller.feeAmount
        feeAmount.unit: BBackend.coinManager.unit
        // TODO feeAmount.fiatValueHuman
        // TODO feeAmount.fiatUnit:
        changeAmount.valueHuman: _tx_controller.changeAmount
        changeAmount.unit: BBackend.coinManager.unit
        // TODO changeAmount.fiatValueHuman
        // TODO changeAmount.fiatUnit:

        onAccepted: {
            if (type === BTxApproveDialog.Type.Prepare) {
                // TODO ask password
                _tx_controller.send()
            }
        }
    }
}
