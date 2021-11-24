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
        onShowMarket: {
            _mainLayout.currentIndex = 1
        }
        onShowAbout: {
            _mainLayout.currentIndex = 2
        }
        onShowSettings: {
            _mainLayout.currentIndex = 3
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
            list.display: _drawer.barsDisplay
        }

        Loader {
            active: _mainLayout.currentIndex === 1
            sourceComponent: BApplicationPage {
                placeholderText: "TODO"
                list.display: _drawer.barsDisplay
            }
        }

        Loader {
            active: _mainLayout.currentIndex === 2
            sourceComponent: BAboutPage {
                list.display: _drawer.barsDisplay
            }
        }

        BSettingsPage {
            list.display: _drawer.barsDisplay
        }
    }

    onClosing: {
        close.accepted = BBackend.onClosing()
    }

    Component.onCompleted: {
        BBackend.onCompleted()
    }
}
