import QtQuick

QtObject {
    property var openedDialogs: ({})

    property Connections backendDialogManager: Connections {
        target: BBackend.dialogManager

        function onOpenDialog(qml_name, options) {
            let dialog = createDialog(qml_name, options["properties"])

            dialog.Component.onDestruction.connect(function () {
                target.onDestruction(options["id"])
            })

            for (let callback_name of options["callbacks"]) {
                dialog[callback_name].connect(function (...args) {
                    target.onResult(options["id"], callback_name, args)
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
            try {
                if (openedDialogs[name] === dialog) {
                    delete openedDialogs[name]
                }
            } catch (e) {}
        })

        return dialog
    }

    function popupDebugMenu() {
        if (BBackend.debug.isEnabled) {
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
