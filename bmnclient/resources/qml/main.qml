import QtQuick 2.15
import QtQuick.Controls.Material 2.15
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
        onExit: {
            // TODO confirmation
            BBackend.exit(0)
        }
    }

    onClosing: {
        if (BBackend.settings.systemTray.closeToTray) {
            close.accepted = false
            showMinimized()
            hide()
        }
    }

    Component.onCompleted: {
        BBackend.onMainWindowCompleted()
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
        target: BBackend.dialogManager

        function onOpenDialog(name, properties) {
            let dialog = _applicationManager.createDialog(name, {})
            for(let callback_name of properties["callbacks"]) {
                dialog[callback_name].connect(function () {
                    target.onResult(name, callback_name)
                })
            }
            dialog.open()
        }
    }
}
