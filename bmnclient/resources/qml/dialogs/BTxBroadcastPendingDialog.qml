import QtQuick
import "../application"
import "../basiccontrols"
import "../coincontrols"

// TODO python control
BDialog {
    id: _base
    property var tx // TxModel
    property var coin // TxModel
    property int visibleAddressCount: Math.min(4, Math.max(tx.inputList.rowCount(), tx.outputList.rowCount()))
    title: qsTr("Transaction is pending...")

    padding: _applicationStyle.padding
    contentItem: BInfoLayout {
        BInfoLabel {
            text: qsTr("Coin:")
        }
        BInfoValue {
            text: _base.coin.fullName
        }
        BInfoSeparator {}

        BInfoLabel {
            text: qsTr("Transaction ID:")
        }
        BInfoValue {
            placeholderText: qsTr("None")
            text: _base.tx.name
        }

        BInfoSeparator {}

        BInfoLabel {
            text: qsTr("Height:")
        }
        BInfoValue {
            text: _base.tx.state.heightHuman
        }
        BInfoSeparator {}

        BInfoLabel {
            text: qsTr("Confirmations:")
        }
        BInfoValue {
            text: _base.tx.state.confirmationsHuman
        }

        BInfoSeparator {}

        BInfoLabel {
            text: qsTr("Amount:")
        }
        BAmountInfoValue {
            amount: _base.tx.amount
        }

        BInfoSeparator {}

        BInfoLabel {
            text: qsTr("Fee:")
        }
        BAmountInfoValue {
            amount: _base.tx.feeAmount
        }
        BInfoSeparator {}

        BInfoLabel {
            text: qsTr("Time:")
        }
        BInfoValue {
            text: _base.tx.state.timeHuman
        }

        BInfoSeparator {}

        BTabBarBox {
            BLayout.columnSpan: parent.columns
            BLayout.fillWidth: true
            BAddressListView {
                property string title: qsTr("Inputs: %1").arg(_base.tx.inputList.rowCountHuman)
                visibleItemCount: _base.visibleAddressCount
                model: _base.tx.inputList
                delegate: BAddressItem {
                    address: model.address
                    amount: model.amount
                    // TODO contextMenu: _base.contextMenu
                }
                templateDelegate: BAddressItem {
                    address: BCommon.addressItemTemplate
                    amount: BCommon.amount
                    // TODO contextMenu: _base.contextMenu
                }
            }
            BAddressListView {
                property string title: qsTr("Outputs: %1").arg(_base.tx.outputList.rowCountHuman)
                visibleItemCount: _base.visibleAddressCount
                model: _base.tx.outputList
                delegate: BAddressItem {
                    address: model.address
                    amount: model.amount
                    // TODO contextMenu: _base.contextMenu
                }
                templateDelegate: BAddressItem {
                    address: BCommon.addressItemTemplate
                    amount: BCommon.amount
                    // TODO contextMenu: _base.contextMenu
                }
            }
        }
        BInfoSeparator {}
    }

    footer: BDialogButtonBox {
        id: _buttonBox
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.RejectRole
            text: BCommon.button.closeRole
        }
    }
}
