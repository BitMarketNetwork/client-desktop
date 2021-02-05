import "../application"
import "../basiccontrols"
import "../coincontrols"

BPane {
    id: _base
    property string title: qsTr("Addresses (%1)").arg(_list.model.rowCountHuman)
    property var coin // CoinListModel item

    contentItem: BAddressListView {
        id: _list
        model: _base.coin.addressList
        delegate: BAddressItem {
            address: model
            contextMenu: _contextMenu
        }
        templateDelegate: BAddressItem {}
    }

    BMenu {
        id: _contextMenu
        property var address // AddressListModel item

        BMenuItem {
            text: qsTr("Copy address")
            onTriggered: {
                BBackend.uiManager.copyToClipboard(_contextMenu.address.name)
            }
        }
        BMenuItem {
            text: qsTr("Edit...")
            onTriggered: {
                // TODO broken api, dont use BBackend.coinManager.coinIndex
                //showAddressDetails(_contextMenu.index)
            }
        }
        BMenuItem {
            text: qsTr("Export transactions")
            onTriggered: {
                // TODO broken api, dont use BBackend.coinManager.coinIndex
                //BBackend.coinManager.exportTransactions(addressIndex)
            }
        }
        BMenuItem {
            text: qsTr("Update")
            enabled: !_contextMenu.address.updating
            onTriggered: {
                // TODO broken api, dont use BBackend.coinManager.coinIndex
                //BBackend.coinManager.updateAddress(addressIndex)
            }
        }
        BMenuItem {
            text: qsTr("Remove address")
            enabled: !_contextMenu.address.updating
            onTriggered: {
                // TODO broken api, dont use BBackend.coinManager.coinIndex
                //BBackend.coinManager.removeAddress(addressIndex)
            }
        }
        BMenuItem {
            text: qsTr("Clear transactions")
            enabled: !_contextMenu.address.updating
            onTriggered: {
                // TODO broken api, dont use BBackend.coinManager.coinIndex
                //BBackend.coinManager.clearTransactions(api.addressIndex)
            }
        }
    }
}
