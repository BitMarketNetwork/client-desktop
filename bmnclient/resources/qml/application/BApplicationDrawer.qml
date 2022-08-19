import QtQuick
import "../basiccontrols"

BNavigationDrawer {
    id: _base
    property int barsDisplay: BNavigationDrawerItem.TextBesideIcon
    property int currentIndex

    signal showContextMenu
    signal showWallet
    signal showChart
    signal showBlockchainExplorer
    signal showMarket
    signal showAbout
    signal showSettings
    signal quit

    BToolButton {
        id: _barsButton
        icon.source: _applicationManager.imagePath("icon-bars.svg")
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
        checked: _base.currentIndex === 0
        text: qsTr("Wallet")
        icon.source: _applicationManager.imagePath("icon-wallet.svg")
        onClicked: {
            _base.showWallet()
        }
    }
    BNavigationDrawerItem {
        checked: _base.currentIndex === 1
        text: qsTr("Chart View")
        icon.source: _applicationManager.imagePath("chart-pie-solid")
        onClicked: {
            _base.showChart()
        }
    }
    BNavigationDrawerItem {
        checked: true
        text: qsTr("Blockchain explorer")
        icon.source: _applicationManager.imagePath("cubes-solid")
        onClicked: {
            _base.showBlockchainExplorer()
        }
    }
    BNavigationDrawerItem {
        checked: _base.currentIndex === 2
        visible: false
        text: qsTr("Market")
        icon.source: _applicationManager.imagePath("icon-market.svg")
        onClicked: {
            _base.showMarket()
        }
    }

    BNavigationDrawerSpacer {}

    BNavigationDrawerItem {
        checked: _base.currentIndex === 3
        text: qsTr("About")
        icon.source: _applicationManager.imagePath("icon-info.svg")
        onClicked: {
            _base.showAbout()
        }
    }
    BNavigationDrawerItem {
        checked: _base.currentIndex === 4
        text: qsTr("Settings")
        icon.source: _applicationManager.imagePath("icon-cog.svg")
        onClicked: {
            _base.showSettings()
        }
    }
    BNavigationDrawerItem {
        text: qsTr("Quit")
        icon.source: _applicationManager.imagePath("icon-quit.svg")
        onClicked: {
            _base.quit()
        }
    }
}
