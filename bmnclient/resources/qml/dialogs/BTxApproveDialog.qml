// JOK++
import QtQuick 2.15
import "../application"
import "../basiccontrols"
import "../coincontrols"

BDialog {
    id: _base
    property var coin // CoinModel

    enum Type {
        Prepare,
        Final
    }

    property int type: BTxApproveDialog.Type.Final

    title: {
        switch (type) {
        case BTxApproveDialog.Type.Prepare:
            return qsTr("Transaction summary")
        case BTxApproveDialog.Type.Final:
            return qsTr("Transaction was sent succefully!")
        }
    }

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
            text: _base.coin.txController.name
        }
        BInfoSeparator {}

        BInfoSeparator {
            transparent: true
        }

        BInfoLabel {
            text: qsTr("Recipient address:")
        }
        BInfoValue {
            text: _base.coin.txController.receiver.addressName
        }
        BInfoSeparator {}

        BInfoLabel {
            text: qsTr("Amount:")
        }
        BAmountInfoValue {
            amount: _base.coin.txController.amount
        }
        BInfoSeparator {}

        BInfoLabel {
            text: qsTr("Fee:")
        }
        BAmountInfoValue {
            amount: _base.coin.txController.feeAmount
        }
        BInfoSeparator {}

        BInfoSeparator {
            transparent: true
        }

        BInfoLabel {
            text: qsTr("Send change to:")
        }
        BInfoValue {
            text: _base.coin.txController.changeAmount.addressName
        }
        BInfoSeparator {}

        BInfoLabel {
            text: qsTr("Change:")
        }
        BAmountInfoValue {
            amount: _base.coin.txController.changeAmount
        }
        BInfoSeparator {}
    }

    footer: BDialogButtonBox {
        id: _buttonBox
        Loader {
            active: _base.type === BTxApproveDialog.Type.Prepare
            sourceComponent: BButton {
                BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
                parent: _buttonBox
                text: qsTr("Broadcast")
            }
            onLoaded: {
                _buttonBox.addItem(item)
            }
        }
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.RejectRole
            text: {
                switch (_base.type) {
                case BTxApproveDialog.Type.Prepare:
                    return BCommon.button.cancelRole
                case BTxApproveDialog.Type.Final:
                    return BCommon.button.closeRole
                }
            }
        }
    }
}
