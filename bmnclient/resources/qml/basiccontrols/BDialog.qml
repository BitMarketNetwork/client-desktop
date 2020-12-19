import QtQuick.Controls 2.15

Dialog {
    property bool dynamicallyCreated: false
    property bool destroyOnClose: true

    closePolicy: Dialog.CloseOnEscape

    parent: Overlay.overlay
    focus: true
    modal: true
    dim: true

    x: Math.round((parent.width - width) / 2)
    y: Math.round((parent.height - height) / 2)

    onClosed: {
        if(destroyOnClose) {
            autoDestroy()
        }
    }

    // TODO Keys.onEnterPressed:
    // TODO Keys.onReturnPressed:

    function autoDestroy() {
        if (dynamicallyCreated) {
            // TODO unknown problem with overlay... the hover effect is lost...
            modal = false
            dim = false
            Qt.callLater(destroy)
        }
    }
}
