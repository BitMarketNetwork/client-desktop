import "../application"
import "../basiccontrols"
import "../coincontrols"

BPane {
    id: _base
    property string title: qsTr("Addresses")
    property BCoinObject coin: null

    contentItem: BAddressListView {
        model: _base.coin.addressListModel
        delegate: BAddressItem {
            address: BAddressObject {
                coin: _base.coin
                name: model.name
                label: model.label
                watchOnly: model.readOnly
                updating: model.isUpdating
                amount.valueHuman: BBackend.settingsManager.coinBalance(model.balance)
                amount.unit: _base.coin.amountUnit // TODO
                amount.fiatValueHuman: model.fiatBalance // TODO
                amount.fiatUnit: _base.coin.fiatAmountUnit // TODO
            }
            contextMenu: _contextMenu
        }
        templateDelegate: BAddressItem {
            address: BAddressObject {
                coin: _base.tx.coin
            }
            contextMenu: _contextMenu
        }
    }

    BMenu {
        id: _contextMenu
        property BAddressObject address: null

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
