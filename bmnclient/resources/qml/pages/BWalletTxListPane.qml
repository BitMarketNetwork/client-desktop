import QtQuick
import "../basiccontrols"
import "../coincontrols"

BPane {
    id: _base
    property string title: qsTr("History (%1)").arg(txList ? txList.rowCountHuman : "")
    property var coin // CoinModel
    property var txList: _base.coin.openTxList(1)

    Component.onDestruction: {
        _base.coin.closeList(_base.txList)
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
