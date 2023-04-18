import QtQuick
import QtQuick.Layouts

import "../basiccontrols"

BComboBox {
    property var stateModel // AbstractTupleStateModel

    Layout.alignment: _applicationStyle.dialogInputAlignment
    Layout.minimumWidth: _applicationStyle.dialogInputWidth
    Layout.preferredWidth: _applicationStyle.dialogInputWidth
    Layout.fillWidth: true

    model: stateModel.list
    valueRole: "name"
    textRole: "fullName"

    Component.onCompleted: {
        currentIndex = indexOfValue(stateModel.currentName)
    }
    onActivated: {
        stateModel.currentName = currentValue
        currentIndex = indexOfValue(stateModel.currentName)
    }
}
