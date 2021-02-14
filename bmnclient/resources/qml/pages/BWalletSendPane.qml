import Bmn 1.0
import "../application"
import "../basiccontrols"
import "../coincontrols"
import "../dialogs"

BPane {
    id: _base
    property string title: qsTr("Send")
    property var coin

    contentItem: BDialogScrollableLayout {
        columns: 3

        BDialogPromtLabel {
            text: qsTr("Coin:")
        }
        BDialogInputLabel {
            BLayout.columnSpan: parent.columns - 1
            text: _base.coin.fullName
        }

        BDialogSeparator {}

        BDialogPromtLabel {
            text: qsTr("Pay to:")
        }
        BDialogInputTextField {
            onTextChanged: {
                if (_tx_controller.receiver.setAddressName(text)) {
                    _receiverAddressValid.status = BDialogValidLabel.Status.Accept
                } else {
                    _receiverAddressValid.status = BDialogValidLabel.Status.Reject
                }
            }
        }
        BDialogValidLabel {
            id: _receiverAddressValid
        }

        BDialogSeparator {}

        BDialogPromtLabel {
            text: qsTr("Available amount:")
        }
        BAmountLabel {
            BLayout.columnSpan: parent.columns - 1
            BLayout.alignment: _applicationStyle.dialogInputAlignment
            orientation: Qt.Horizontal
            amount: _tx_controller.availableAmount
        }

        BDialogPromtLabel {
            text: qsTr("Amount:")
        }
        BAmountInput {
            id: _amount
            BLayout.alignment: _applicationStyle.dialogInputAlignment
            orientation: Qt.Horizontal
            amount: _tx_controller.amount
        }
        BDialogValidLabel {
            status: _amount.validStatus
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
                        text: BStandardText.button.resetRole
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
