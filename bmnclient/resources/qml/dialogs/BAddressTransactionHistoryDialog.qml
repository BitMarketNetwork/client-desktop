import QtQuick
import "../application"
import "../basiccontrols"
import "../coincontrols"

BDialog {
    id: _base
    property var address // AddressModel
    property var txList: address.openTxList(1)

    Component.onDestruction: {
        address.closeList(txList)
    }

    title: qsTr("Transaction history")
    contentItem: BAddressTxListView {
        model: _base.txList
    }
    footer: BDialogButtonBox {
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
            text: BCommon.button.closeRole
        }
    }
}
