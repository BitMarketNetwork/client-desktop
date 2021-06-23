import QtQml 2.15
import QtQuick 2.15
import QtQuick.Window 2.15
import "../application"
import "../basiccontrols"
import "../dialogs"

QtObject {
    property var openedDialogs: ({})

    property Connections backendDialogManager: Connections {
        target: BBackend.dialogManager

        function onOpenDialog(name, properties) {
            let dialog = createDialog(name, {})
            for (let callback_name of properties["callbacks"]) {
                dialog[callback_name].connect(function () {
                    target.onResult(name, callback_name)
                })
            }
            dialog.open()
        }
    }

    function imagePath(path) {
        return Qt.resolvedUrl("../../images/" + path)
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
                _applicationWindow,
                "../dialogs/" + name + ".qml",
                Object.assign({}, properties, { "dynamicallyCreated": true }))

        dialog.onOpened.connect(function () {
            let oldDialog = openedDialogs[name]
            openedDialogs[name] = dialog
            if (oldDialog !== undefined) {
                oldDialog.close()
            }
        })

        dialog.onClosed.connect(function () {
            if (openedDialogs[name] === dialog) {
                delete openedDialogs[name]
            }
        })

        return dialog
    }

    function createMessageDialog(text, type) {
        let dialog = createDialog(
                "BMessageDialog", {
                    "text": text,
                    "type": !type ? BMessageDialog.Type.Information : type
                })
        return dialog
    }

    function openRevealSeedPharseDialog() { // TODO create dialogs/*.qml file
        let passwordDialog = createDialog("BPasswordDialog", {})
        passwordDialog.onPasswordAccepted.connect(function (password) {
            let dialog = createDialog(
                    "BSeedPhraseDialog", {
                        "type": BSeedPhraseDialog.Type.Reveal,
                        "seedPhraseText": BBackend.keyStore.revealSeedPhrase(password),
                        "readOnly": !BBackend.isDebugMode
                    })
            dialog.open()
        })
        passwordDialog.open()
    }

    function popupDebugMenu() {
        if (BBackend.isDebugMode) {
            let menu = createObject(_applicationWindow, "BDebugMenu.qml", {})
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
}
