import QtQuick 2.15
import "../application"
import "../basiccontrols"
import "../coincontrols"

BApplicationPage {
    id: _base

    title: qsTr("Wallet")
    placeholderText: qsTr("Select coin from the left list.")

    list.model: BBackend.coinManager.coinModel
    list.delegate: BCoinItem {
        visible: model.visible
        enabled: model.enabled
        coin: BCoinObject {
            shortName: model.shortName
            fullName: model.fullName
            iconPath: _applicationManager.imagePath(model.iconPath)

            index: model.index
            amount.valueHuman: BBackend.settingsManager.coinBalance(model.balance) // TODO move to BWalletCoinPane?
            amount.unit: BBackend.settingsManager.coinUnit(model.unit) // TODO
            amount.fiatValueHuman: model.fiatBalance // TODO kill char '$' // TODO move to BWalletCoinPane?
            amount.fiatUnit: "USD" // TODO BBackend.coinManager.currency
            addressListModel: model.addressModel
            txListModel: BBackend.coinManager.txModel
        }

        onClicked: {
            BBackend.coinManager.coinIndex = coin.index // TODO kill
            _base.stack.currentIndex = _base.coinIndexToListIndex(coin.index)
            _base.stack.children[_base.stack.currentIndex].active = true
        }
    }

    Repeater {
        model: BBackend.coinManager.coinModel
        delegate: Loader {
            readonly property int coinIndex: model.index
            active: false
            sourceComponent: BWalletCoinPage {
                coin: BCoinObject {
                    shortName: model.shortName
                    fullName: model.fullName
                    iconPath: _applicationManager.imagePath(model.iconPath)

                    index: model.index
                    amount.valueHuman: BBackend.settingsManager.coinBalance(model.balance) // TODO move to BWalletCoinPane?
                    amount.unit: BBackend.settingsManager.coinUnit(model.unit) // TODO
                    amount.fiatValueHuman: model.fiatBalance // TODO kill char '$' // TODO move to BWalletCoinPane?
                    amount.fiatUnit: "USD" // TODO BBackend.coinManager.currency
                    addressListModel: model.addressModel
                    txListModel: BBackend.coinManager.txModel
                }

                onGenerateAddress: {
                    _base.generateAddress(coin)
                }
                onAddWatchOnlyAddress: {
                    _base.addWatchOnlyAddress(coin)
                }
            }
        }
    }

    function generateAddress(coin) {
        let dialog = _applicationManager.createDialog(
                "BAddressEditDialog", {
                    "coin": coin,
                    "type": BAddressEditBox.Type.Generate
                })
        dialog.onAccepted.connect(function () {
            // TODO dialog.commentText
            BBackend.coinManager.makeAddress(coin.index, dialog.labelText, dialog.useSegwit)
        })
        dialog.open()
    }

    function addWatchOnlyAddress(coin) {
        let dialog = _applicationManager.createDialog(
                "BAddressEditDialog", {
                    "coin": coin,
                    "type": BAddressEditBox.Type.AddWatchOnly
                })
        dialog.onAccepted.connect(function () {
            // TODO dialog.commentText
            BBackend.coinManager.addWatchAddress(coin.index, dialog.addressText, dialog.labelText)
        })
        dialog.open()
    }

    // TODO
    /*function editAddress(coin, addressIndex) {
        var address = BBackend.coinManager.coin.wallets[addressIndex]
        let mPage = pushPage("ExportAddressPage.qml", {
                                 "wif": address.to_wif,
                                 "pub": address.public_key,
                                 "address": address.name,
                                 "label": address.label,
                                 "message": address.message,
                                 "created": address.created_str
                             })
        mPage.onClosed.connect(function () {
            address.label = mPage.label
            address.save() // local slot!!?
        })

        let dialog = _applicationManager.createDialog(
                "BAddressEditDialog", {
                    "coin": coin,
                    "type": BAddressEditBox.Type.Generate
                })
        dialog.onAccepted.connect(function () {
            // TODO dialog.commentText
            BBackend.coinManager.makeAddress(coin.index, dialog.labelText, dialog.useSegwit)
        })
        dialog.open()
    }*/

    function coinIndexToListIndex(coinIndex) {
        for (let i = 0; i < stack.count; ++i) {
            let item = stack.itemAt(i)
            if (typeof item.coinIndex !== "undefined" && item.coinIndex === coinIndex) {
                return i
            }
        }
        return 0
    }
}
