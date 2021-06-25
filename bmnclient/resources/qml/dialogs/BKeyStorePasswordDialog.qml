import "../application"
import "../basiccontrols"

BPasswordDialog {
    id: _base

    signal resetWalletAccepted

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
