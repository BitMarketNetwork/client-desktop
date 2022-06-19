import QtQuick
import "../application"
import "../basiccontrols"
import "../coincontrols"
import "../dialogs"

BPane {
    id: _base
    property string title: qsTr("Send")
    property var coin // CoinModel

    contentItem: BDialogScrollableLayout {
        columns: 3

        BDialogPromptLabel {
            text: qsTr("Coin:")
        }
        BDialogInputLabel {
            BLayout.columnSpan: parent.columns - 1
            text: _base.coin.fullName
        }

        BDialogSeparator {}

        BDialogPromptLabel {
            text: qsTr("Pay to:")
        }
        BDialogInputTextField {
            id: _inputRecipientAddress
            text: ""
            onTextEdited: {
                _base.coin.txFactory.receiver.addressName = text
            }
            onTextChanged: {
                _base.coin.txFactory.receiver.addressName = text
            }

        }
        BDialogValidLabel {
            status: _base.coin.txFactory.receiver.validStatus
        }

        BDialogPromptLabel {
            text: qsTr("Pay from (optional):")
        }
        BDialogInputTextField {
            id: _inputSourceAddress
            text: _base.coin.txFactory.receiver.inputAddressName
            readOnly: true
            onTextChanged: {
                _base.coin.txFactory.receiver.inputAddressName = text
            }
        }
        BDialogValidLabel {
            status: BCommon.ValidStatus.Unset // TODO
        }

        BDialogSeparator {}

        BDialogPromptLabel {
            text: qsTr("Available amount:")
        }
        BAmountLabel {
            BLayout.columnSpan: parent.columns - 1
            BLayout.alignment: _applicationStyle.dialogInputAlignment
            orientation: Qt.Horizontal
            amount: _base.coin.txFactory.availableAmount
        }

        BDialogPromptLabel {
            text: qsTr("Amount:")
        }
        BAmountInput {
            id: _inputAmount1
            BLayout.alignment: _applicationStyle.dialogInputAlignment
            orientation: Qt.Horizontal
            amount: _base.coin.txFactory.receiverAmount
            enabled: _base.coin.txFactory.receiver.validStatus && _inputRecipientAddress.length > 0
        }
        BDialogValidLabel {
            status: _base.coin.txFactory.receiverAmount.validStatus
        }

        BDialogSeparator {}

        BDialogPromptLabel {
            text: qsTr("Transaction fee:")
        }
        BAmountLabel {
            BLayout.columnSpan: parent.columns - 1
            BLayout.alignment: _applicationStyle.dialogInputAlignment
            orientation: Qt.Horizontal
            amount: _base.coin.txFactory.feeAmount
        }

        BDialogSeparator {}

        BSpoilerItem {
            BLayout.columnSpan: parent.columns

            headerItem: BRowLayout {
                BLabel {
                    text: qsTr("Advanced options:")
                }
            }
            contentItem: BDialogLayout {
                columns: 3
                clip: true

                BDialogPromptLabel {
                    text: qsTr("Price per kilobyte:")
                }
                BAmountInput {
                    BLayout.alignment: _applicationStyle.dialogInputAlignment
                    orientation: Qt.Horizontal
                    amount: _base.coin.txFactory.kibFeeAmount
                    defaultButtonText: qsTr("Recommended")
                    enabled: _base.coin.txFactory.receiver.validStatus && _inputRecipientAddress.length > 0
                }
                BDialogValidLabel {
                    status: _base.coin.txFactory.kibFeeAmount.validStatus
                }
                BDialogPromptLabel {
                    text: qsTr("Subtract fee from amount:")
                }
                BDialogInputSwitch {
                    BLayout.columnSpan: parent.columns - 1
                    checked: _base.coin.txFactory.feeAmount.subtractFromAmount
                    onCheckedChanged: {
                        _base.coin.txFactory.feeAmount.subtractFromAmount = checked
                    }
                }

                BDialogSeparator {}

                BDialogPromptLabel {
                    text: qsTr("Raw size / Virtual size:")
                }
                BDialogInputLabel {
                    BLayout.columnSpan: parent.columns - 1
                    text: qsTr("%1 / %2 bytes")
                            .arg(_base.coin.txFactory.state.estimatedRawSizeHuman)
                            .arg(_base.coin.txFactory.state.estimatedVirtualSizeHuman)
                }
                BDialogPromptLabel {
                    text: qsTr("Change:")
                }
                BAmountLabel {
                    BLayout.columnSpan: parent.columns - 1
                    BLayout.alignment: _applicationStyle.dialogInputAlignment
                    orientation: Qt.Horizontal
                    amount: _base.coin.txFactory.changeAmount
                }
            }
        }

        BDialogSeparator {}

        // TODO temporary disabled
        /*BDialogPromptLabel {
            text: qsTr("Send change to new address:")
        }
        BDialogInputSwitch {
            BLayout.columnSpan: parent.columns - 1
            checked: _base.coin.txFactory.changeAmount.toNewAddress
            onCheckedChanged: {
                _base.coin.txFactory.changeAmount.toNewAddress = checked
            }
        }

        BDialogSeparator {}

        BDialogPromptLabel {}
        BDialogInputButton {
            BLayout.columnSpan: parent.columns - 1
            text: "Select inputs..."
            onClicked: {
                _inputListDialog.open()
            }
        }*/

        BDialogInputButtonBox {
            BButton {
                BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
                text: qsTr("Prepare...")
                enabled: _base.coin.txFactory.isValid
            }
            BButton {
                BDialogButtonBox.buttonRole: BDialogButtonBox.ResetRole
                text: BCommon.button.resetRole
            }
            onReset: {
                _base.clear()
            }
            onAccepted: {
                if (_base.coin.txFactory.isValid && _base.coin.txFactory.prepare() && _base.coin.txFactory.sign()) {
                    BBackend.keyStore.onPrepareTransaction(_base.coin)
                }
            }
        }
    }

    BTxSourceListDialog {
        id: _inputListDialog
        sourceList: _base.coin.txFactory.sourceList
        onClosed: {
            // TODO _base.coin.txFactory.recalcSources()
        }
    }

    function clear() {
        _inputRecipientAddress.clear()
        _inputSourceAddress.clear()
        _inputAmount1.clear()
        _inputAmount2.clear()
    }
}
