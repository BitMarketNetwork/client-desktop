import "../application"

BNewPasswordDialog {
    destroyOnClose: false

    onPasswordAccepted: {
        if (!BBackend.keyStore.create(password)) {
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
