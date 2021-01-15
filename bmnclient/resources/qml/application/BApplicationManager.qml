import QtQml 2.15
import QtQuick 2.15
import QtQuick.Window 2.15
import "../application"
import "../basiccontrols"
import "../dialogs"

QtObject {
    property BApplicationWindow applicationWindow: null

    function quit() {
        Qt.quit() // TODO
    }

    function imageSource(filePath) {
        return Qt.resolvedUrl("../../images/" + filePath)
    }
    function coinImageSource(shortName) {
        return Qt.resolvedUrl("../../images/coins/" + shortName + ".svg")
    }

    function createObject(parent, filePath, properties) {
        let component = Qt.createComponent(filePath)
        if (component.status === Component.Error) {
            console.error(component.errorString())
            return null
        }

        let object = component.createObject(parent, properties)
        object.Component.onDestruction.connect(function () {
            console.debug("~" + filePath)
        })
        return object
    }

    function createDialog(name, properties) {
        let dialog = createObject(
                applicationWindow,
                "../dialogs/" + name + ".qml",
                Object.assign({}, properties, { "dynamicallyCreated": true }))
        return dialog
    }

    function messageDialog(text, buttons) {
        let dialog = createDialog(
                "BMessageDialog", {
                    "text": text,
                    "standardButtons": !buttons ? BMessageDialog.Ok : buttons
                })
        return dialog
    }

    function openAplhaDialog(onAccepted, onRejected) {
        let dialog = createDialog("BAlphaDialog", {})
        dialog.onAccepted.connect(onAccepted)
        dialog.onRejected.connect(onRejected)
        dialog.open()
    }

    function openKeyStorePasswordDialog() {
        let dialog
        if (BBackend.keyStore.hasPassword) {
            dialog = createDialog("BKeyStorePasswordDialog", {})
            dialog.onResetWalletAccepted.connect(openKeyStorePasswordDialog)
        } else {
            dialog = createDialog("BKeyStoreNewPasswordDialog", {})
            dialog.onPasswordReady.connect(openKeyStorePasswordDialog)
        }
        dialog.onRejected.connect(quit)
        dialog.open()
    }

    function openRevealSeedPharseDialog() { // TODO create dialogs/*.qml file
        let passwordDialog = createDialog("BPasswordDialog", {})
        passwordDialog.onPasswordAccepted.connect(function (password) {
            let dialog = createDialog(
                    "BSeedPhraseDialog", {
                        "type": BSeedPhraseDialog.Type.Reveal,
                        "seedPhraseText": BBackend.keyStore.revealSeedPhrase(password),
                        "readOnly": !BBackend.debugMode
                    })
            dialog.open()
        })
        passwordDialog.open()
    }

    function popupDebugMenu() {
        if (BBackend.debugMode) {
            let menu = createObject(applicationWindow, "BDebugMenu.qml", {})
            if (menu !== null) {
                menu.onClosed.connect(function () {
                    Qt.callLater(menu.destroy)
                })
                menu.popup()
            }
         }
    }

    function calcPopupPosition(parent, popupWidth, popupHeight) {
        let point = parent.mapToItem(parent.Window.window.contentItem, 0, 0)
        point.x = point.x + (parent.width - parent.rightPadding) - popupWidth
        point.y = point.y + (parent.height - parent.bottomPadding)

        if (point.y + popupHeight >= parent.Window.window.contentItem.height) {
            point.y =
                    point.y
                    - (parent.height - parent.bottomPadding)
                    + parent.topPadding
                    - popupHeight
        }
        return parent.mapFromItem(parent.Window.window.contentItem, point)
    }

    function integerToLocaleString(value) {
        return Number(value).toLocaleString(_applicationWindow.locale, 'f', 0)
    }
}
