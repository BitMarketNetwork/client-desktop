import QtQuick
import "../application"
import "../basiccontrols"
import "../coincontrols"

// TODO python control
BDialog {
    id: _base
    property var tx // TxModel
    property var coin // TxModel
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

        BTxIoView {
            BLayout.columnSpan: parent.columns
            BLayout.fillWidth: true
            tx: _base.tx
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
