import "../application"

BNewPasswordDialog {
    destroyOnClose: false

    onPasswordAccepted: {
        console.assert(!BBackend.keyManager.hasPassword)
        if (!BBackend.keyManager.setNewPassword(password)) {
            // TODO internal error, show it
            open()
            return
        }
        console.assert(BBackend.keyManager.hasPassword)

        autoDestroy()
        passwordReady()
    }

    onRejected: {
        autoDestroy()
    }
}
