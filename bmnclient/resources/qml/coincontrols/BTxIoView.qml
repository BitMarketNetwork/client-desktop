import QtQuick
import "../application"
import "../basiccontrols"

BTabBarBox {
    id: _base
    property var tx // TxModel
    property var inputList: tx.openInputList(1)
    property var outputList: tx.openOutputList(1)
    property int visibleAddressCount: Math.min(
        4,
        Math.max(inputList ? inputList.rowCount() : 0, outputList ? outputList.rowCount() : 0))

    Component.onDestruction: {
        tx.closeList(inputList)
        tx.closeList(outputList)
    }

    BAddressListView {
        property string title: qsTr("Inputs: %1").arg(_base.inputList ? _base.inputList.rowCountHuman : "")
        visibleItemCount: _base.visibleAddressCount
        model: _base.inputList
        delegate: BAddressItem {
            address: modelObject.address
            amount: modelObject.amount
            // TODO contextMenu: _base.contextMenu
        }
        templateDelegate: BAddressItem {
            address: BCommon.addressItemTemplate
            amount: BCommon.amountTemplate
            // TODO contextMenu: _base.contextMenu
        }
    }
    BAddressListView {
        property string title: qsTr("Outputs: %1").arg(_base.outputList ? _base.outputList.rowCountHuman : "")
        visibleItemCount: _base.visibleAddressCount
        model: _base.outputList
        delegate: BAddressItem {
            address: modelObject.address
            amount: modelObject.amount
            // TODO contextMenu: _base.contextMenu
        }
        templateDelegate: BAddressItem {
            address: BCommon.addressItemTemplate
            amount: BCommon.amountTemplate
            // TODO contextMenu: _base.contextMenu
        }
    }
}
