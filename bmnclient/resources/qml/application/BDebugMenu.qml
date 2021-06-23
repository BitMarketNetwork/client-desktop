import "../basiccontrols"

BMenu {
    readonly property string notificationMessage: "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore..."

    title: "Debug"

    BMenu {
        title: "Coins"
        BMenuItem {
            text: "Increase height"
            onTriggered: {
                BBackend.debugManager.increaseHeight(1)
            }
        }
        BMenuItem {
            text: "Decrease height"
            onTriggered: {
                BBackend.debugManager.increaseHeight(-1)
            }
        }
    }
    BMenu {
        title: "Notification test"
        BMenuItem {
            text: "Icon: none"
            onTriggered: {
                BBackend.debugManager.notify(notificationMessage, "n")
            }
        }
        BMenuItem {
            text: "Icon: information"
            onTriggered: {
                BBackend.debugManager.notify(notificationMessage, "i")
            }
        }
        BMenuItem {
            text: "Icon: warning"
            onTriggered: {
                BBackend.debugManager.notify(notificationMessage, "w")
            }
        }
        BMenuItem {
            text: "Icon: error"
            onTriggered: {
                BBackend.debugManager.notify(notificationMessage, "e")
            }
        }
        BMenuItem {
            text: "Icon: all"
            onTriggered: {
                BBackend.debugManager.notify(notificationMessage, "n")
                BBackend.debugManager.notify(notificationMessage, "i")
                BBackend.debugManager.notify(notificationMessage, "w")
                BBackend.debugManager.notify(notificationMessage, "e")
            }
        }
    }
}
