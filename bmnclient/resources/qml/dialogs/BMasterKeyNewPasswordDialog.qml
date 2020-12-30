import "../application"

BNewPasswordDialog {
    destroyOnClose: false

    onPasswordAccepted: {
        if (!BBackend.rootKey.createPassword(password)) {
            // TODO internal error, show it
            open()
            return
        }

        autoDestroy()
        passwordReady()
    }

    onRejected: {
        autoDestroy()
    }
}
