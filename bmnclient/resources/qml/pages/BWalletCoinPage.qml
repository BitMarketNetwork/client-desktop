import "../basiccontrols"
import "../coincontrols"

BControl {
    id: _base
    property var coin // CoinListModel item

    signal generateAddress
    signal addWatchOnlyAddress

    contentItem: BColumnLayout {
        BCoinHeader {
            id: _header
            BLayout.fillWidth: true
            coin: _base.coin
            contextMenu: _contextMenu
        }
        BTabBarBox {
            BLayout.fillWidth: true
            BLayout.fillHeight: true
            spacing: _applicationStyle.spacing

            BWalletAddressListPane {
                coin: _base.coin
            }
            BWalletTxListPane {
                coin: _base.coin
            }
            BWalletSendPane {
                coin: _base.coin
            }
            BWalletReceivePane {
                coin: _base.coin
            }
        }
    }

    BMenu {
        id: _contextMenu
        BMenuItem {
            text: qsTr("Generate a new address...")
            onTriggered: {
                _base.generateAddress()
            }
        }
        BMenuItem {
            text: qsTr("Add a watch only address...")
            onTriggered: {
                _base.addWatchOnlyAddress()
            }
        }
    }
}
