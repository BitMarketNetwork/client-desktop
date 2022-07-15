import QtQuick
import QtQuick.Controls.Material
import "application"
import "basiccontrols"
import "pages"

BApplicationWindow {
    id: _applicationWindow

    title: BBackend.title

    BApplicationStyle {
        id: _applicationStyle
    }

    BApplicationManager {
        id: _applicationManager
    }

    background: Rectangle {
        color: Qt.darker(Material.backgroundColor, _applicationStyle.backgroundDarkFactor)
    }

    header: BApplicationDrawer {
        id: _drawer
        onShowContextMenu: {
            _applicationManager.popupDebugMenu()
        }
        onShowWallet: {
            _mainLayout.currentIndex = 0
        }
        onShowChart: {
            _mainLayout.currentIndex = 1
        }
        onShowBlockchainExplorer: {
            _mainLayout.currentIndex = 2
        }
        onShowMarket: {
            _mainLayout.currentIndex = 3
        }
        onShowAbout: {
            _mainLayout.currentIndex = 4
        }
        onShowSettings: {
            _mainLayout.currentIndex = 5
        }
        onQuit: {
            BBackend.onQuitRequest()
        }
    }

    BStackLayout {
        id: _mainLayout
        anchors.fill: parent
        currentIndex: 0

        BWalletPage {
            id: _walletPage
            list.display: _drawer.barsDisplay
        }

        Loader {
            active: _mainLayout.currentIndex === 1
            sourceComponent: BChartPage {
                onSliceClicked: (label) => {
                    _mainLayout.currentIndex = 0
                    _walletPage.setCurrentCoin(label)
                }
            }
        }

        Loader {
            active: _mainLayout.currentIndex === 2
            sourceComponent: BBlockchainExplorerPage {}
        }

        Loader {
            active: _mainLayout.currentIndex === 3
            sourceComponent: BApplicationPage {
                placeholderText: "TODO"
                list.display: _drawer.barsDisplay
            }
        }

        Loader {
            active: _mainLayout.currentIndex === 4
            sourceComponent: BAboutPage {
                list.display: _drawer.barsDisplay
            }
        }

        BSettingsPage {
            list.display: _drawer.barsDisplay
        }
    }

    onClosing: function(close) {
        close.accepted = BBackend.onClosing()
    }

    Component.onCompleted: {
        BBackend.onCompleted()
    }
}
