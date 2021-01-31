import "../application"
import "../basiccontrols"
import "../coincontrols"

BPane {
    id: _base
    property string title: qsTr("History")
    property var coin // CoinListModel item

    contentItem: BTxListView {
        model: _base.coin.txListModel
        delegate: BTxItem {
            tx: model
            contextMenu: _contextMenu
        }
    }

    BMenu {
        id: _contextMenu
        property BTxObject tx: null

        BMenuItem {
            text: "TODO" // TODO
        }
    }
}
