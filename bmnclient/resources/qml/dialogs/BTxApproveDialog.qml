import QtQuick 2.15
import "../application"
import "../basiccontrols"
import "../coincontrols"

BDialog {
    id: _base

    enum Type {
        Prepare,
        Final
    }

    property int type: BTxApproveDialog.Type.Final
    property var coin
    property alias txText: _tx.text
    property alias targetAddressText: _targetAddress.text
    property alias changeAddressText: _changeAddress.text
    property alias amount: _amount.amount
    property alias feeAmount: _feeAmount.amount
    property alias changeAmount: _changeAmount.amount

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
            id: _tx
            placeholderText: qsTr("None")
        }
        BInfoSeparator {}

        BInfoSeparator {
            transparent: true
        }

        BInfoLabel {
            text: qsTr("Recipient address:")
        }
        BInfoValue {
            id: _targetAddress
        }
        BInfoSeparator {}

        BInfoLabel {
            text: qsTr("Amount:")
        }
        BAmountInfoValue {
            id: _amount
        }
        BInfoSeparator {}

        BInfoLabel {
            text: qsTr("Fee:")
        }
        BAmountInfoValue {
            id: _feeAmount
        }
        BInfoSeparator {}

        BInfoSeparator {
            transparent: true
        }

        BInfoLabel {
            text: qsTr("Send change to:")
        }
        BInfoValue {
            id: _changeAddress
        }
        BInfoSeparator {}

        BInfoLabel {
            text: qsTr("Change:")
        }
        BAmountInfoValue {
            id: _changeAmount
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
