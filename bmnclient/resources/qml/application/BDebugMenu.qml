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
        title: "Notification test"
        BMenuItem {
            text: "Icon: none"
            onTriggered: {
                BBackend.debug.notify(notificationMessage, "n")
            }
        }
        BMenuItem {
            text: "Icon: information"
            onTriggered: {
                BBackend.debug.notify(notificationMessage, "i")
            }
        }
        BMenuItem {
            text: "Icon: warning"
            onTriggered: {
                BBackend.debug.notify(notificationMessage, "w")
            }
        }
        BMenuItem {
            text: "Icon: error"
            onTriggered: {
                BBackend.debug.notify(notificationMessage, "e")
            }
        }
        BMenuItem {
            text: "Icon: all"
            onTriggered: {
                BBackend.debug.notify(notificationMessage, "n")
                BBackend.debug.notify(notificationMessage, "i")
                BBackend.debug.notify(notificationMessage, "w")
                BBackend.debug.notify(notificationMessage, "e")
            }
        }
    }
}
