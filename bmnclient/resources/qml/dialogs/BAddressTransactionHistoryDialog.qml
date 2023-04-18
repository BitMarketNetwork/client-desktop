import "../application"
import "../basiccontrols"
import "../coincontrols"
import "../dialogcontrols"

BDialog {
    id: _base
    property var address // AddressModel

    title: qsTr("Transaction history")
    contentItem: BAddressTxListView {
        id: _list
        model: _base.address.txList
    }
    footer: BDialogButtonBox {
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
            text: BCommon.button.closeRole
        }
    }
}
