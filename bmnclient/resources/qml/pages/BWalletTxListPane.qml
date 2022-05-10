import QtQuick
import "../basiccontrols"
import "../coincontrols"

BPane {
    id: _base
    property string title: qsTr("History (%1)").arg(txList ? txList.rowCountHuman : "")
    property var coin // CoinModel
    property var txList: coin.openTxList(1)

    Component.onDestruction: {
        coin.closeList(txList)
    }

    contentItem: BTxListView {
        model: _base.txList
        delegate: BTxItem {
            tx: modelObject
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
