import QtQuick.Layouts

import "../basiccontrols"

BLabel {
    Layout.columnSpan: parent.columns
    Layout.alignment: _applicationStyle.dialogDescriptionAlignment
    Layout.minimumWidth: _applicationStyle.dialogInputWidth
    Layout.preferredWidth: _applicationStyle.dialogInputWidth
    Layout.fillWidth: true

    wrapMode: BLabel.Wrap
}
