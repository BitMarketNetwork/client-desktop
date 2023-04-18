import QtQuick.Layouts

import "../basiccontrols"

BTextArea {
    Layout.alignment: _applicationStyle.dialogInputAlignment
    Layout.minimumWidth: _applicationStyle.dialogInputWidth
    Layout.preferredWidth: _applicationStyle.dialogInputWidth
    Layout.fillWidth: true
}
