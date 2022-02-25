import "../application"
import "../basiccontrols"

BTabBarBox {
    id: _base
    property var tx // TxModel
    property int visibleAddressCount: Math.min(
        4,
        Math.max(tx.inputList.rowCount(), tx.outputList.rowCount()))

    BAddressListView {
        property string title: qsTr("Inputs: %1").arg(_base.tx.inputList.rowCountHuman)
        visibleItemCount: _base.visibleAddressCount
        model: _base.tx.inputList
        delegate: BAddressItem {
            address: model.address
            amount: model.amount
            // TODO contextMenu: _base.contextMenu
        }
        templateDelegate: BAddressItem {
            address: BCommon.addressItemTemplate
            amount: BCommon.amountTemplate
            // TODO contextMenu: _base.contextMenu
        }
    }
    BAddressListView {
        property string title: qsTr("Outputs: %1").arg(_base.tx.outputList.rowCountHuman)
        visibleItemCount: _base.visibleAddressCount
        model: _base.tx.outputList
        delegate: BAddressItem {
            address: model.address
            amount: model.amount
            // TODO contextMenu: _base.contextMenu
        }
        templateDelegate: BAddressItem {
            address: BCommon.addressItemTemplate
            amount: BCommon.amountTemplate
            // TODO contextMenu: _base.contextMenu
        }
    }
}
