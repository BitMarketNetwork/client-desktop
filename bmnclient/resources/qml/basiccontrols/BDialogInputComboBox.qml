import QtQuick

BComboBox {
    property var stateModel // AbstractTupleStateModel

    BLayout.alignment: _applicationStyle.dialogInputAlignment
    BLayout.minimumWidth: _applicationStyle.dialogInputWidth
    BLayout.preferredWidth: _applicationStyle.dialogInputWidth
    BLayout.fillWidth: true

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
