import "../application"
import "../basiccontrols"
import "../coincontrols"
import "../dialogs"

BPane {
    id: _base
    property string title: qsTr("Addresses (%1)").arg(_list.model.rowCountHuman)
    property var coin // CoinModel

    contentItem: BAddressListView {
        id: _list
        model: _base.coin.addressList
        delegate: BAddressItem {
            address: model
            amount: model.balance
            contextMenu: _contextMenu
        }
        templateDelegate: BAddressItem {
            address: BCommon.addressItemTemplate
            amount: BCommon.addressItemTemplate.balance
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
