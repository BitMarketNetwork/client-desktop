import "../application"
import "../basiccontrols"

BPasswordDialog {
    id: _base

    signal resetWalletAccepted

    destroyOnClose: false

    onPasswordAccepted: {
        if (!BBackend.rootKey.setPassword(password)) {
            let dialog = _applicationManager.messageDialog(qsTr("Wrong password."))
            dialog.onClosed.connect(_base.open)
            dialog.open()
            return
        }

        if (!BBackend.uiManager.dbValid) { // TODO whats it?
            let dialog = _applicationManager.messageDialog(
                    qsTr(
                        "Your current database version isn't supported in this application version (%1).\n"
                        + "You can reset your database either use old application version.\n\n"
                        + "Your master key won't be deleted.\n"
                        + "In case you reset databse you should wait some time to sinchornize data.\n\n" + "Reset database?").arg(
                        Qt.application.version),
                    BMessageDialog.Yes | BMessageDialog.No)
            dialog.onAccepted.connect(function () {
                BBackend.uiManager.resetDB() // TODO if failed?
                _base.autoDestroy()
                // TODO unknown action, not tested
            })
            dialog.onRejected.connect(_base.open)
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
                BBackend.rootKey.resetPassword() // TODO if failed?
                _base.autoDestroy()
                _base.resetWalletAccepted()
            })
            dialog.onRejected.connect(_base.open)
            dialog.open()
        }
    }
}
