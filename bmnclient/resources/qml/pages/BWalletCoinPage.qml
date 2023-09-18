import QtQuick.Layouts

import "../basiccontrols"
import "../coincontrols"

BControl {
    id: _base
    property var coin // CoinModel

    signal createAddress
    signal createWatchOnlyAddress

    contentItem: BColumnLayout {
        BCoinHeader {
            id: _header
            Layout.fillWidth: true
            coin: _base.coin
            contextMenu: _contextMenu
        }
        BTabBarBox {
            id: _tabBar
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: _applicationStyle.spacing

            BWalletAddressListPane {
                coin: _base.coin

                onSpendFromTriggered: {
                    _tabBar.currentIndex = 2
                }
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
            text: qsTr("Create a new address...")
            onTriggered: {
                _base.createAddress()
            }
        }
        BMenuItem {
            text: qsTr("Add a watch only address...")
            onTriggered: {
                _base.createWatchOnlyAddress()
            }
        }
    }
}
