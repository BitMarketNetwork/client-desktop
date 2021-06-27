import "../basiccontrols"

BPasswordDialog {
    id: _base
    signal resetWalletAccepted

    title: qsTr("Open Key Store")

    BDialogSeparator {}
    BDialogDescription {
        text:
            qsTr("Forgot your password?")
            + " <a href=\"#\">" + qsTr("Reset wallet") + "</a>"
        onLinkActivated: {
            _base.close()
            _base.resetWalletAccepted()
        }
    }
}
