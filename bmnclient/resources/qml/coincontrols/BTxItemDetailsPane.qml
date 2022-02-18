import QtQuick
import QtQuick.Controls.Material
import "../application"
import "../basiccontrols"
import "../coincontrols"

BPane {
    id: _base
    property var tx // TxModel
    property int visibleAddressCount: Math.min(4, Math.max(tx.inputList.rowCount(), tx.outputList.rowCount()))

    Material.elevation: 1 // for background, view QtQuick/Controls.2/Material/Pane.qml
    padding: _applicationStyle.padding
    contentItem: BInfoLayout {
        BInfoLabel {
            text: qsTr("Height:")
        }
        BInfoValue {
            text: _base.tx.state.heightHuman
        }
        BInfoSeparator {}

        BInfoLabel {
            text: qsTr("Confirmations:")
        }
        BInfoValue {
            text: _base.tx.state.confirmationsHuman
        }
        BInfoSeparator {}

        BInfoLabel {
            text: qsTr("Fee:")
        }
        BAmountInfoValue {
            amount: _base.tx.feeAmount
        }
        BInfoSeparator {}

        BTabBarBox {
            BLayout.columnSpan: parent.columns
            BLayout.fillWidth: true
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
        BInfoSeparator {}
    }
}
