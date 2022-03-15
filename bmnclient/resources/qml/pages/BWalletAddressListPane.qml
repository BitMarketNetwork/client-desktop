import "../application"
import "../basiccontrols"
import "../coincontrols"
import "../dialogs"
import QtQuick

BPane {
    id: _base
    property string title: qsTr("Addresses (%1)").arg(_tableView.model.rowCountHuman)
    property var coin // CoinModel
    
    BHorizontalHeaderView {
        id: _horizontalHeader
        syncView: _tableView
        anchors.left: _tableView.left
        width: parent.width

        model: ObjectModel {
            id: itemModel
            BLabel {
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                text: qsTr("Address")
            }
            BLabel {
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                text: qsTr("Label")
            }
            BLabel {
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                text: qsTr("Balance")
            }
            BLabel {
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                text: qsTr("Tx count")
            }
        }
    }
    BAddressTableView {
        id: _tableView
        anchors.fill: parent
        anchors.topMargin: _horizontalHeader.height
        model: _base.coin.addressList

        property var columnWidths: [30, 50, 10, 5, 5] // %
        
        columnWidthProvider: function (column) { 
            if (_tableView.model) {
                return (_tableView.width * columnWidths[column]) / 100
            } else {
                return 0
            }
        }
        onWidthChanged: _tableView.forceLayout()
        delegate: BAddressTableRow {
            implicitWidth: _tableView.columnWidthProvider(column)
            address: model
            amount: model.balance
            contextMenu: _contextMenu
        }
    }

    BMenu {
        id: _contextMenu
        property var address // AddressModel

        BMenuItem {
            text: qsTr("Copy address")
            onTriggered: {
                BBackend.clipboard.text = _contextMenu.address.name
            }
        }
        BMenuItem {
            text: qsTr("Spend from")
            onTriggered: {
                _contextMenu.address.state.isTxInput = true
            }
        }
        BMenuItem {
            text: qsTr("Transaction history")
            onTriggered: {
                let dialog = _applicationManager.createDialog(
                    "BAddressTransactionHistoryDialog", {
                    "address" : _contextMenu.address,
                    "height" : _applicationWindow.height / 2,
                    "width" : _applicationWindow.width / 2
                })
                dialog.open();
            }
        }
        /*BMenuItem {
            text: qsTr("Edit...")
            onTriggered: {
                // TODO
                //showAddressDetails(_contextMenu.index)
            }
        }*/
        /*BMenuItem {
            text: qsTr("Export transactions")
            onTriggered: {
                // TODO
                //BBackend.coinManager.exportTransactions(addressIndex)
            }
        }*/
        /*BMenuItem {
            text: qsTr("Update")
            //enabled: !_contextMenu.address.updating
            onTriggered: {
                // TODO
                //BBackend.coinManager.updateAddress(addressIndex)
            }
        }*/
        /*BMenuItem {
            text: qsTr("Remove address")
            //enabled: !_contextMenu.address.updating
            onTriggered: {
                // TODO
                //BBackend.coinManager.removeAddress(addressIndex)
            }
        }*/
        /*BMenuItem {
            text: qsTr("Clear transactions")
            //enabled: !_contextMenu.address.updating
            onTriggered: {
                // TODO
                //BBackend.coinManager.clearTransactions(api.addressIndex)
            }
        }*/
    }
}
