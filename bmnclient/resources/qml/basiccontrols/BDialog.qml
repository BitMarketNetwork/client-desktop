import QtQuick 2.15
import QtQuick.Controls 2.15

Dialog {
    id: _base
    property bool dynamicallyCreated: false
    property var context: null // ui.qml.dialogs.AbstractDialog

    closePolicy: Dialog.CloseOnEscape

    parent: Overlay.overlay
    focus: true
    modal: true
    dim: true

    x: Math.round((parent.width - width) / 2)
    y: Math.round((parent.height - height) / 2)

    // TODO temporary fix: Binding loop detected for property "implicitWidth"
    // when: contentItem == BDialogLayout and header.elide != Text.ElideNone
    // qt5/qtquickcontrols2/src/imports/controls/material/Dialog.qml
    implicitWidth: Math.max(implicitBackgroundWidth + leftInset + rightInset,
                            contentWidth + leftPadding + rightPadding,
                            //implicitHeaderWidth,
                            implicitFooterWidth)

    onClosed: {
        if (dynamicallyCreated) {
            // TODO unknown problem with overlay... the hover effect is lost...
            modal = false
            dim = false
            Qt.callLater(destroy)
        }
    }

    // TODO Keys.onEnterPressed:
    // TODO Keys.onReturnPressed:

    // connections with ui.qml.dialogs.AbstractDialog
    Loader {
        active: _base.context !== null
        sourceComponent: Connections {
            target: _base.context

            function onForceActiveFocus() {
                _base.forceActiveFocus()
            }
            function onReject() {
                _base.reject()
            }
            function onClose() {
                _base.close()
            }
        }
    }
}
