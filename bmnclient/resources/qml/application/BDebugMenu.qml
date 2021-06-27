import "../basiccontrols"

BMenu {
    readonly property string notificationMessage: "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore..."

    title: "Debug"

    BMenu {
        title: "Coins"
        BMenuItem {
            text: "Increase height"
            onTriggered: {
                BBackend.debug.increaseHeight(1)
            }
        }
        BMenuItem {
            text: "Decrease height"
            onTriggered: {
                BBackend.debug.increaseHeight(-1)
            }
        }
    }
    BMenu {
        title: "Show message test"
        BMenuItem {
            text: "Icon: information"
            onTriggered: {
                BBackend.debug.showMessage("i", notificationMessage)
            }
        }
        BMenuItem {
            text: "Icon: warning"
            onTriggered: {
                BBackend.debug.showMessage("w", notificationMessage)
            }
        }
        BMenuItem {
            text: "Icon: error"
            onTriggered: {
                BBackend.debug.showMessage("e", notificationMessage)
            }
        }
        BMenuItem {
            text: "Icon: all"
            onTriggered: {
                BBackend.debug.showMessage("i", notificationMessage)
                BBackend.debug.showMessage("w", notificationMessage)
                BBackend.debug.showMessage("e", notificationMessage)
            }
        }
    }
}
