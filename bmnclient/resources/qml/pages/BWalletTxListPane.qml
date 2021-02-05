import "../application"
import "../basiccontrols"
import "../coincontrols"

BPane {
    id: _base
    property string title: qsTr("History (%1)").arg(_list.model.rowCountHuman)
    property var coin // CoinListModel item

    contentItem: BTxListView {
        id: _list
        model: _base.coin.txList
        delegate: BTxItem {
            tx: model
            contextMenu: _contextMenu
        }
    }

    BMenu {
        id: _contextMenu
        property var tx

        BMenuItem {
            text: "TODO" // TODO
        }
    }
}
