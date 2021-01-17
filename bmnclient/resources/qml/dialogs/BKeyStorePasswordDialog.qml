import "../application"
import "../basiccontrols"

BPasswordDialog {
    id: _base

    signal resetWalletAccepted

    destroyOnClose: false

    onPasswordAccepted: {
        if (!BBackend.keyStore.applyPassword(password)) {
            let dialog = _applicationManager.messageDialog(qsTr("Wrong password."))
            dialog.onClosed.connect(_base.open)
            dialog.open()
            return
        }
        autoDestroy()
        passwordReady()
    }

    onRejected: {
        autoDestroy()
    }

    BDialogSeparator {}
    BDialogDescription {
        text:
            qsTr("Forgot your password?")
            + " <a href=\"#\">" + qsTr("Reset wallet") + "</a>"
        onLinkActivated: {
            _base.close()

            let dialog = _applicationManager.messageDialog(
                    qsTr(
                        "This will destroy all saved information and you can lose your money!\n"
                        + "Please make sure you remember the seed phrase.\n\n"
                        + "Reset?"),
                    BMessageDialog.Yes | BMessageDialog.No)
            dialog.onAccepted.connect(function () {
                BBackend.keyStore.resetPassword() // TODO if failed?
                _base.autoDestroy()
                _base.resetWalletAccepted()
            })
            dialog.onRejected.connect(_base.open)
            dialog.open()
        }
    }
}
