import QtQuick 2.15
import QtQuick.Controls.Material 2.15
import "application"
import "basiccontrols"
import "pages"

BApplicationWindow {
    id: _applicationWindow

    title: BBackend.uiManager.title
    visible: true // TODO wrong usage, should controlled by Python

    BApplicationStyle {
        id: _applicationStyle
        applicationWindow: _applicationWindow
    }

    BApplicationManager {
        id: _applicationManager
        applicationWindow: _applicationWindow
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
        onExit: {
            // TODO confirmation
            _applicationManager.exit()
        }
    }

    onClosing: {
        if (BBackend.settingsManager.hideToTray) {
            close.accepted = false
            showMinimized()
            hide()
        }
    }

    onVisibleChanged: {
        BBackend.uiManager.visible = visible
    }

    Component.onCompleted: {
        // TODO should controlled by Python
        _applicationManager.openAplhaDialog(
                    _applicationManager.openKeyStorePasswordDialog,
                    _applicationManager.quit)
        BBackend.coinManager.showEmptyBalances = true // TODO
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

    Connections {
        target: BBackend.uiManager
        function onShow() {
            _applicationWindow.showNormal()
            _applicationWindow.raise()
            _applicationWindow.requestActivate()
        }
        function onHide() {
            _applicationWindow.hide()
        }
    }

    Connections {
        target: BBackend.keyStore
        function onMnemoRequested() { // TODO bad name
            let dialog = _applicationManager.createDialog("BNewSeedDialog", {})
            dialog.onRejected.connect(_applicationManager.exit)
            dialog.open()
        }
    }
}
