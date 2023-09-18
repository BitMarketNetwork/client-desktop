import QtQuick
import QtQuick.Controls

import "../basiccontrols"

DialogButtonBox {
    // block standardButtons
    delegate: BButton {
        Component.onCompleted: {
            text = "standardButtons are not implemented"
        }
    }
}
