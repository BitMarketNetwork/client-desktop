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

        BRowLayout {
            id: _advancedOptions
            state: _spoiler.checked ? "EXPANDED" : "COLLAPSED"
            BLayout.columnSpan: parent.columns

            BUnfoldToolButton {
                id: _spoiler
            }
            BLabel {
                text: qsTr("Advanced options:")
            }

            property variant targets: [ _pricePkLabel, _inputAmount2, _validLabel1,
                                        _subtractLabel, _inputSwitch, _sizesLabel,
                                        _bytesLabel, _changeLabel, _amountLabel,
                                        _inputSeparator ]
            states: [
                State { name: "EXPANDED" },
                State { name: "COLLAPSED" }
            ]

            transitions: [
                Transition {
                    from: "EXPANDED"
                    to: "COLLAPSED"

                    SequentialAnimation {
                        id: collapseAnimation
                        ParallelAnimation {
                            BNumberAnimation { targets: _advancedOptions.targets; property: "opacity"; to: 0 }
                        }
                        ParallelAnimation {
                            BNumberAnimation { target: _optSeparator; property: "BLayout.preferredHeight"; to: target.implicitHeight }
                            BNumberAnimation { targets: _advancedOptions.targets; property: "BLayout.preferredHeight"; to: 0 }
                        }
                        BNumberAnimation { target: _optSeparator; property: "opacity"; to: 1 }
                    }
                },
                Transition {
                    from: "COLLAPSED"
                    to: "EXPANDED"

                    SequentialAnimation {
                        BNumberAnimation { target: _optSeparator; property: "opacity"; to: 0 }
                        ParallelAnimation {
                            BNumberAnimation { target: _pricePkLabel;   property: "BLayout.preferredHeight"; to: target.implicitHeight  }
                            BNumberAnimation { target: _inputAmount2;   property: "BLayout.preferredHeight"; to: target.implicitHeight  }
                            BNumberAnimation { target: _validLabel1;    property: "BLayout.preferredHeight"; to: target.implicitHeight  }
                            BNumberAnimation { target: _subtractLabel;  property: "BLayout.preferredHeight"; to: target.implicitHeight  }
                            BNumberAnimation { target: _inputSwitch;    property: "BLayout.preferredHeight"; to: target.implicitHeight  }
                            BNumberAnimation { target: _sizesLabel;     property: "BLayout.preferredHeight"; to: target.implicitHeight  }
                            BNumberAnimation { target: _bytesLabel;     property: "BLayout.preferredHeight"; to: target.implicitHeight  }
                            BNumberAnimation { target: _changeLabel;    property: "BLayout.preferredHeight"; to: target.implicitHeight  }
                            BNumberAnimation { target: _amountLabel;    property: "BLayout.preferredHeight"; to: target.implicitHeight  }
                            BNumberAnimation { target: _inputSeparator; property: "BLayout.preferredHeight"; to: target.implicitHeight  }
                            BNumberAnimation { target: _optSeparator;   property: "BLayout.preferredHeight"; to: 0 }
                        }
                        ParallelAnimation {
                            BNumberAnimation { targets: _advancedOptions.targets; property: "opacity"; to: 1 }
                        }
                    }
                }
            ]
        }
        BDialogSeparator {
            id: _optSeparator
        }

        BDialogPromptLabel {
            id: _pricePkLabel
            BLayout.preferredHeight: 0
            opacity: 0
            text: qsTr("Price per kilobyte:")
        }
        BAmountInput {
            id: _inputAmount2
            BLayout.preferredHeight: 0
            BLayout.alignment: _applicationStyle.dialogInputAlignment
            opacity: 0
            orientation: Qt.Horizontal
            amount: _base.coin.txFactory.kibFeeAmount
            defaultButtonText: qsTr("Recommended")
            enabled: _base.coin.txFactory.receiver.validStatus && _inputRecipientAddress.length > 0
        }
        BDialogValidLabel {
            id: _validLabel1
            BLayout.preferredHeight: 0
            opacity: 0
            status: _base.coin.txFactory.kibFeeAmount.validStatus
        }

        BDialogPromptLabel {
            id: _subtractLabel
            BLayout.preferredHeight: 0
            opacity: 0
            text: qsTr("Subtract fee from amount:")
        }
        BDialogInputSwitch {
            id: _inputSwitch
            BLayout.preferredHeight: 0
            BLayout.columnSpan: parent.columns - 1
            opacity: 0
            checked: _base.coin.txFactory.feeAmount.subtractFromAmount
            onCheckedChanged: {
                _base.coin.txFactory.feeAmount.subtractFromAmount = checked
            }
        }

        BDialogSeparator {
            id: _inputSeparator
            opacity: 0
            BLayout.preferredHeight: 0
        }

        BDialogPromptLabel {
            id: _sizesLabel
            BLayout.preferredHeight: 0
            opacity: 0
            text: qsTr("Raw size / Virtual size:")
        }
        BDialogInputLabel {
            id: _bytesLabel
            BLayout.preferredHeight: 0
            BLayout.columnSpan: parent.columns - 1
            opacity: 0
            text: qsTr("%1 / %2 bytes")
                    .arg(_base.coin.txFactory.state.estimatedRawSizeHuman)
                    .arg(_base.coin.txFactory.state.estimatedVirtualSizeHuman)
        }

        BDialogPromptLabel {
            id: _changeLabel
            BLayout.preferredHeight: 0
            opacity: 0
            text: qsTr("Change:")
        }
        BAmountLabel {
            id: _amountLabel
            BLayout.preferredHeight: 0
            BLayout.columnSpan: parent.columns - 1
            BLayout.alignment: _applicationStyle.dialogInputAlignment
            opacity: 0
            orientation: Qt.Horizontal
            amount: _base.coin.txFactory.changeAmount
        }

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
                    let dialog = _applicationManager.createDialog(
                                "BTxApproveDialog", {
                                    "type": BTxApproveDialog.Type.Prepare,
                                    "coin": _base.coin
                                })
                    dialog.onAccepted.connect(function () {
                        if (_base.coin.txFactory.broadcast()) { // TODO error?
                                _base.clear()
                        } else {
                            // TODO error?
                        }
                    })
                    dialog.open()
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
