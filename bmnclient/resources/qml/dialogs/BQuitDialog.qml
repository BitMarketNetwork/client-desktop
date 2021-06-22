BMessageDialog {
    title: qsTr("Quit")
    text: qsTr("Do you want to quit %1?").arg(Qt.application.name)
    type: BMessageDialog.Type.AskYesNo
}
