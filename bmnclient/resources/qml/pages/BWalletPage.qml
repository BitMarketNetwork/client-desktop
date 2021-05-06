import QtQuick 2.15
import "../application"
import "../basiccontrols"
import "../coincontrols"

BApplicationPage {
    id: _base

    title: qsTr("Wallet")
    placeholderText: qsTr("Select coin from the left list.")

    list.model: BBackend.coinList
    list.delegate: BCoinItem {
        visible: model.state.visible
        enabled: model.state.visible
        coin: model
        onClicked: {
            _base.stack.currentIndex = _base.coinIndexToListIndex(coin.index)
            _base.stack.children[_base.stack.currentIndex].active = true
        }
    }

    Repeater {
        model: BBackend.coinList
        delegate: Loader {
            readonly property int coinIndex: model.index
            active: false
            sourceComponent: BWalletCoinPage {
                coin: model
                onCreateAddress: {
                    _base.createAddress(coin)
                }
                onCreateWatchOnlyAddress: {
                    _base.createWatchOnlyAddress(coin)
                }
            }
        }
    }

    function createAddress(coin) {
        let dialog = _applicationManager.createDialog(
                "BAddressEditDialog", {
                    "coin": coin,
                    "type": BAddressEditBox.Type.Create
                })
        dialog.onAccepted.connect(function () {
            coin.manager.createAddress(dialog.isSegwit, dialog.labelText, dialog.commentText)
            // TODO show result
        })
        dialog.open()
    }

    function createWatchOnlyAddress(coin) {
        let dialog = _applicationManager.createDialog(
                "BAddressEditDialog", {
                    "coin": coin,
                    "type": BAddressEditBox.Type.CreateWatchOnly
                })
        dialog.onAccepted.connect(function () {
            coin.manager.createWatchOnlyAddress(dialog.addressNameText, dialog.labelText, dialog.commentText)
            // TODO show result
        })
        dialog.open()
    }

    // TODO
    /*function editAddress(coin, addressIndex) {
        var address = BBackend.coinManager.coin.addressList[addressIndex]
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
                    "type": BAddressEditBox.Type.Create
                })
        dialog.onAccepted.connect(function () {
            // TODO dialog.commentText
            coin.manager.createAddress(coin.index, dialog.labelText, dialog.isSegwit)
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
