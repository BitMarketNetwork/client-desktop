import QtQuick
import QtQuick.Layouts

import "../application"
import "../basiccontrols"
import "../coincontrols"
import "../dialogcontrols"

BDialog {
    id: _base
    property var tx // TxModel
    property var coin // CoinModel
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
            text: qsTr("Broadcast time:")
        }
        BInfoValue {
            text: _base.tx.state.timeHuman
        }
        BInfoSeparator {}

        BTxIoView {
            Layout.columnSpan: parent.columns
            Layout.fillWidth: true
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
