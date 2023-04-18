import QtQuick.Layouts

import "../basiccontrols"

BLabel {
    Layout.alignment: _applicationStyle.dialogInputAlignment
    Layout.minimumWidth: implicitWidth
    Layout.fillWidth: true

    font.bold: true
}
