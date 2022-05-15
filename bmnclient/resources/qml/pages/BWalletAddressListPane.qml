import QtQuick
import "../application"
import "../basiccontrols"
import "../coincontrols"
import "../dialogs"

BPane {
    id: _base
    property string title: qsTr("Addresses (%1)").arg(addressList ? addressList.rowCountHuman : "")
    property var coin // CoinModel
    property var addressList: coin.openAddressList(5)

    signal spendFromTriggered

    Component.onDestruction: {
         coin.closeList(addressList)
    }

    BHorizontalHeaderView {
        id: _horizontalHeader
        syncView: _tableView
        anchors.left: _tableView.left
        width: parent.width

        model: ObjectModel {
            id: itemModel

            BControl {
                BLabel {
                    anchors.centerIn: parent
                    text: qsTr("Address")
                }
            }
            BControl {
                BLabel {
                    anchors.centerIn: parent
                    text: qsTr("Label")
                }
            }
            BControl {
                BLabel {
                    anchors.centerIn: parent
                    text: qsTr("Balance")
                }
            }
            BControl {
                BLabel {
                    anchors.centerIn: parent
                    text: qsTr("Tx")
                }
            }
        }
        // TODO sorting controls
    }
    BAddressTableView {
        id: _tableView
        anchors.fill: parent
        anchors.topMargin: _horizontalHeader.implicitHeight
        model: _base.addressList

        columnWidth: [355, -1, 150, 65, 60]

        delegate: BAddressTableRow {
            implicitWidth: _tableView.columnWidthProvider(column)
            address: modelObject
            amount: modelObject.balance
            contextMenu: _contextMenu

            Rectangle { // col separator
                anchors.right: parent.right
                width: 1
                height: parent.height
                color: "grey"
                opacity: 0.5
            }
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
                _base.coin.txFactory.receiver.inputAddressName = _contextMenu.address.name
                spendFromTriggered()
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
