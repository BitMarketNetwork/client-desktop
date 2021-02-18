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
                _tx_controller.model.receiver.setAddressName(text)
            }
        }
        BDialogValidLabel {
            status: _tx_controller.model.receiver.validStatus
        }

        BDialogSeparator {}

        BDialogPromtLabel {
            text: qsTr("Available amount:")
        }
        BAmountLabel {
            BLayout.columnSpan: parent.columns - 1
            BLayout.alignment: _applicationStyle.dialogInputAlignment
            orientation: Qt.Horizontal
            amount: _tx_controller.model.availableAmount
        }

        BDialogPromtLabel {
            text: qsTr("Amount:")
        }
        BAmountInput {
            BLayout.alignment: _applicationStyle.dialogInputAlignment
            orientation: Qt.Horizontal
            amount: _tx_controller.model.amount
        }
        BDialogValidLabel {
            status: _tx_controller.model.amount.validStatus
        }

        BDialogSeparator {}

        BDialogPromtLabel {
            text: qsTr("Transaction fee:")
        }
        BAmountLabel {
            BLayout.columnSpan: parent.columns - 1
            BLayout.alignment: _applicationStyle.dialogInputAlignment
            orientation: Qt.Horizontal
            amount: _tx_controller.model.feeAmount
        }

        BDialogPromtLabel {
            text: qsTr("per kilobyte:")
        }
        BAmountInput {
            BLayout.alignment: _applicationStyle.dialogInputAlignment
            orientation: Qt.Horizontal
            amount: _tx_controller.model.kibFeeAmount
            defaultButtonText: qsTr("Recommended")
        }
        BDialogValidLabel {
            status: _tx_controller.model.kibFeeAmount.validStatus
        }

        BDialogPromtLabel {
            text: qsTr("Subtract fee from amount:")
        }
        BDialogInputSwitch {
            BLayout.columnSpan: parent.columns - 1
            checked: _tx_controller.model.feeAmount.subtractFromAmount
            onCheckedChanged: {
                _tx_controller.model.feeAmount.setSubtractFromAmount(checked)
            }
        }

        BDialogSeparator {}

        BDialogPromtLabel {
            text: qsTr("Change:")
        }
        BAmountLabel {
            BLayout.columnSpan: parent.columns - 1
            BLayout.alignment: _applicationStyle.dialogInputAlignment
            orientation: Qt.Horizontal
            amount: _tx_controller.model.changeAmount
        }

        BDialogPromtLabel {
            text: qsTr("Send change to new address:")
        }
        BDialogInputSwitch {
            BLayout.columnSpan: parent.columns - 1
            checked: _tx_controller.model.changeAmount.toNewAddress
            onCheckedChanged: {
                _tx_controller.model.changeAmount.setToNewAddress(checked)
            }
        }

        BDialogSeparator {}

        BDialogPromtLabel {}
        BDialogInputButton {
            BLayout.columnSpan: parent.columns - 1
            text: "Select inputs..."
            onClicked: {
                        _inputListDialog.open()
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
