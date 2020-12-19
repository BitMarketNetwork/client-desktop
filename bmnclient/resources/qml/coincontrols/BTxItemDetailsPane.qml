import QtQuick 2.15
import QtQuick.Controls.Material 2.15
import "../basiccontrols"
import "../coincontrols"

BPane {
    id: _base
    property BTxObject tx: null
    property int visibleAddressCount: {
        let rowCount = Math.max(
                _base.tx.inputAddressListModel.rowCount(),
                _base.tx.outputAddressListModel.rowCount())
        return Math.min(2, rowCount)
    }

    Material.elevation: 1 // for background, view QtQuick/Controls.2/Material/Pane.qml
    padding: _applicationStyle.padding
    contentItem: BInfoLayout {
        BInfoLabel {
            text: qsTr("Height:")
        }
        BInfoValue {
            text: tx.height
        }
        BInfoSeparator {}

        BInfoLabel {
            text: qsTr("Confirmations:")
        }
        BInfoValue {
            text: tx.confirmationCount
        }
        BInfoSeparator {}

        BInfoLabel {
            text: qsTr("Fee:")
        }
        BAmountInfoValue {
            amount: tx.feeAmount
        }
        BInfoSeparator {}

        BTabBarBox {
            BLayout.columnSpan: parent.columns
            BLayout.fillWidth: true
            BAddressListView {
                property string title: qsTr("Inputs: %1").arg(_base.tx.inputAddressListModel.rowCount()) // TODO number format
                visibleItemCount: _base.visibleAddressCount
                model: _base.tx.inputAddressListModel
                delegate: BAddressItem {
                    address: BAddressObject {
                        coin: _base.tx.coin
                        name: model.addressName
                        label: model.index
                        watchOnly: false
                        updating: false
                        amount.valueHuman: model.amountHuman
                        amount.unit: _base.coin.amountUnit // TODO
                        amount.fiatValueHuman: model.fiatBalance // TODO
                        amount.fiatUnit: _base.coin.fiatAmountUnit // TODO
                    }
                    // TODO contextMenu: _base.contextMenu
                }
                templateDelegate: BAddressItem {
                    address: BAddressObject {
                        coin: _base.tx.coin
                    }
                    // TODO contextMenu: _base.contextMenu
                }
            }
            BAddressListView {
                property string title: qsTr("Outputs: %1").arg(_base.tx.outputAddressListModel.rowCount()) // TODO number format
                visibleItemCount: _base.visibleAddressCount
                model: _base.tx.outputAddressListModel
                delegate: BAddressItem {
                    address: BAddressObject {
                        coin: _base.tx.coin
                        name: model.addressName
                        label: model.index
                        watchOnly: false
                        updating: false
                        amount.valueHuman: model.amountHuman
                        amount.unit: _base.coin.amountUnit // TODO
                        amount.fiatValueHuman: model.fiatBalance // TODO
                        amount.fiatUnit: _base.coin.fiatAmountUnit // TODO
                    }
                    // TODO contextMenu: _base.contextMenu
                }
                templateDelegate: BAddressItem {
                    address: BAddressObject {
                        coin: _base.tx.coin
                    }
                    // TODO contextMenu: _base.contextMenu
                }
            }
        }
        BInfoSeparator {}
    }
}
