import "../basiccontrols"

BDialog {
    property alias text: _message.text

    title: Qt.application.name
    contentItem: BDialogLayout {
        columns: 1
        BDialogDescription {
            id: _message
        }
    }

    // TODO my buttons text for standardButtons
    standardButtons: BDialog.Ok
    footer: BDialogButtonBox {}
}
