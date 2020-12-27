import "../application"

BNewPasswordDialog {
    destroyOnClose: false

    onPasswordAccepted: {
        if (!BBackend.keyManager.createPassword(password)) {
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
