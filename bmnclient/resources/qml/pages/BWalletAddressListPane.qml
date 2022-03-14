import "../application"
import "../basiccontrols"
import "../coincontrols"
import "../dialogs"
import QtQuick

BPane {
    id: _base
    property string title: qsTr("Addresses (%1)").arg(_list.model.rowCountHuman)
    property var coin // CoinModel

    contentItem: BAddressListView {
        id: _list
        model: _base.coin.addressList
        delegate: BAddressTableRow{
            address: model
            amount: model.balance
            contextMenu: _contextMenu
        }
        templateDelegate: BAddressTableRow {
            address: BCommon.addressItemTemplate
            amount: BCommon.addressItemTemplate.balance
        }
        header: BRowLayout {
            width: _list.width
            height: 50
            
            Item {
                BLayout.preferredWidth: parent.width * 0.20
                BLayout.maximumWidth: parent.width * 0.20
                BLayout.fillHeight: true

                BLabel {
                    anchors.centerIn: parent
                    text: qsTr("Address")
                }
            }
            Item {
                BLayout.preferredWidth: parent.width * 0.10
                BLayout.maximumWidth: parent.width * 0.10
                BLayout.fillHeight: true

                BLabel {
                    anchors.centerIn: parent
                    text: qsTr("Label")
                }
            }
            Item { //spacer
                BLayout.preferredWidth: parent.width * 0.50
                BLayout.maximumWidth: parent.width * 0.50
                BLayout.fillHeight: true
            }
            Item {
                BLayout.preferredWidth: parent.width * 0.05
                BLayout.maximumWidth: parent.width * 0.05
                BLayout.fillHeight: true

                BLabel {
                    //anchors.verticalCenter: parent.verticalCenter
                    //anchors.right: parent.right
                    anchors.centerIn: parent
                    text: qsTr("Balance")
                }
            }
            Item {
                BLayout.preferredWidth: parent.width * 0.05
                BLayout.maximumWidth: parent.width * 0.05
                BLayout.fillHeight: true

                BLabel {
                    anchors.centerIn: parent
                    text: qsTr("Tx")
                }
            }

            Item { //spacer
                BLayout.preferredWidth: parent.width * 0.05
                BLayout.maximumWidth: parent.width * 0.05
                BLayout.fillHeight: true
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
