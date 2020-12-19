import QtQuick 2.15
import "../basiccontrols"

BNavigationDrawer {
    id: _base
    property int barsDisplay: BNavigationDrawerItem.TextBesideIcon

    signal showContextMenu
    signal showWallet
    signal showMarket
    signal showAbout
    signal showSettings
    signal quit

    BToolButton {
        id: _barsButton
        icon.source: _applicationManager.imageSource("icon-bars.svg")
        onClicked: {
            if (_base.barsDisplay === BNavigationDrawerItem.TextBesideIcon) {
                _base.barsDisplay = BNavigationDrawerItem.IconOnly
            } else {
                _base.barsDisplay = BNavigationDrawerItem.TextBesideIcon
            }
        }
    }
    BLogoImage {
        BLayout.rightMargin: _barsButton.implicitWidth + parent.spacing
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onClicked: {
                mouse.accepted = true
                switch (mouse.button) {
                case Qt.RightButton:
                    _base.showContextMenu()
                    break
                }
            }
        }
    }

    BNavigationDrawerItem {
        checked: true
        text: qsTr("Wallet")
        icon.source: _applicationManager.imageSource("icon-wallet.svg")
        onClicked: {
            _base.showWallet()
        }
    }
    BNavigationDrawerItem {
        text: qsTr("Market")
        icon.source: _applicationManager.imageSource("icon-market.svg")
        onClicked: {
            _base.showMarket()
        }
    }

    BNavigationDrawerSpacer {}

    BNavigationDrawerItem {
        text: qsTr("About")
        icon.source: _applicationManager.imageSource("icon-info.svg")
        onClicked: {
            _base.showAbout()
        }
    }
    BNavigationDrawerItem {
        text: qsTr("Settings")
        icon.source: _applicationManager.imageSource("icon-cog.svg")
        onClicked: {
            _base.showSettings()
        }
    }
    BNavigationDrawerItem {
        text: qsTr("Quit")
        icon.source: _applicationManager.imageSource("icon-quit.svg")
        onClicked: {
            _base.quit()
        }
    }
}
