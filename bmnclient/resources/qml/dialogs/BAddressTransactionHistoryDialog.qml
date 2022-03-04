import "../application"
import "../basiccontrols"
import "../coincontrols"

BDialog {
    id: _base
    property var coin // CoinModel

    title: qsTr("Transaction history")
    contentItem: BAddressTxListView {
        id: _list
        model: _base.coin.txList // TODO _base.address.txList 
    }
    footer: BDialogButtonBox {
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
            text: BCommon.button.closeRole
        }
    }
}