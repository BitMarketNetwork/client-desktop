import "../application"
import "../basiccontrols"
import "../coincontrols"

BDialog {
    id: _base
    property var coin // CoinModel
    property var address

    title: qsTr("Transaction history")
    contentItem: BAddressTxListView {
        id: _list
        model: _base.coin.txList // TODO _base.address.txList 
        coinName: _base.coin.name
    }
    footer: BDialogButtonBox {
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
            text: BCommon.button.closeRole
        }
    }
}