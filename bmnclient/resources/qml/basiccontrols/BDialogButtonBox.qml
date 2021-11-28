import QtQuick
import QtQuick.Controls

DialogButtonBox {
    // block standardButtons
    delegate: BButton {
        Component.onCompleted: {
            text = "standardButtons are not implemented"
        }
    }
}
