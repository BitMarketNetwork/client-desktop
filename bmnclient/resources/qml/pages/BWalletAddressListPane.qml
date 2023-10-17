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

    BWalletAddressTable {
        id: _tableItem
        anchors.fill: parent
        model: _base.addressList
    }

    BMenu {
        id: _contextMenu
        property var address // AddressModel

        BMenuItem {
            text: qsTr("Edit...")
            onTriggered: {
                let dialog = _applicationManager.createDialog(
                "BAddressEditDialog", {
                    "coin": coin,
                    "type": BAddressEditBox.Type.Edit,
                    "addressNameText": _contextMenu.address.name,
                    "labelText": _contextMenu.address.state.label
                    //"commentText": _contextMenu.address.comment
                })
                dialog.open()
            }
        }

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
