import QtQuick
import "../application"
import "../basiccontrols"
import "../coincontrols"

// TODO: Use BlockchainExplorer python model
BApplicationPage {
    id: _base

    title: qsTr("Wallet")
    placeholderText: qsTr("Select coin from the left list.")

    readonly property var supportedCoins: [ 'btc' ]

    list.model: BBackend.coinList
    list.delegate: BCoinItem {
        visible: supportedCoins.includes(coin.name)
        enabled: model.state.isEnabled
        coin: model
        onClicked: {
            _base.stack.currentIndex = _base.coinToListIndex(coin.name)
            _base.stack.children[_base.stack.currentIndex].active = true
        }
    }

    Repeater {
        model: BBackend.coinList
        delegate: Loader {
            readonly property string coinName: model.name
            active: false
            sourceComponent: BExplorerItem {
                anchors.fill: parent
                coin: model
            }
        }
    }

    function coinToListIndex(coinName) {
        for (let i = 0; i < stack.count; ++i) {
            let item = stack.itemAt(i)
            if (typeof item.coinName !== "undefined" && item.coinName === coinName) {
                return i
            }
        }
        return 0
    }
}
