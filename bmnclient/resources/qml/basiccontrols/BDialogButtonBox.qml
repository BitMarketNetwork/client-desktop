import QtQuick 2.15
import QtQuick.Controls 2.15

DialogButtonBox {
    // block standardButtons
    delegate: BButton {
        Component.onCompleted: {
            text = "standardButtons are not implemented"
        }
    }
}
