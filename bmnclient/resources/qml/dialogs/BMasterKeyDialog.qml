import "../application"
import "../basiccontrols"

BDialog {
    id: _base

    destroyOnClose: false
    title: qsTr("Master key generation")

    contentItem: BDialogLayout {
        columns: 1

        // TODO advanced welcome text

        BDialogInputRadioButton {
            id: _generateButton
            text: qsTr("Generate new master key")
            checked: true
        }
        BDialogInputRadioButton {
            id: _restoreButton
            text: qsTr("Restore from seed phrase")
        }
        BDialogInputRadioButton {
            id: _restoreBackupButton
            text: qsTr("Restore wallet from backup")
        }
    }

    footer: BDialogButtonBox {
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
            text: BStandardText.buttonText.continueRole
        }
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.RejectRole
            text: BStandardText.buttonText.cancelRole
        }
    }

    onAccepted: {
        if (_generateButton.checked) {
            _generateDialog.open()
        } else if (_restoreButton.checked) {
            _restoreDialog.open()
        } else if (_restoreBackupButton.checked) {
            // TODO Segmentation fault
            if (!BBackend.keyManager.importWallet()) {
                // TODO
                //console.log("Import error")
                open()
            } else {
                autoDestroy()
            }
        } else {
            autoDestroy()
        }
    }

    onRejected: {
        autoDestroy()
    }

    BSeedPhraseDialog {
        id: _generateDialog
        type: BSeedPhraseDialog.Type.Generate
        readOnly: !BBackend.debugMode
        seedPhraseText: BBackend.keyManager.getInitialPassphrase(salt)
        enableAccept: true

        onSaltChanged: {
            seedPhraseText = BBackend.keyManager.getInitialPassphrase(salt)
        }
        onAccepted: {
            BBackend.keyManager.preparePhrase(seedPhraseText) // TODO if fail?
            _validateDialog.open()
        }
        onRejected: {
            _base.open()
        }
    }

    BSeedPhraseDialog {
        id: _validateDialog
        type: BSeedPhraseDialog.Type.Validate
        readOnly: false

        onSeedPhraseTextChanged: {
            enableAccept = (seedPhraseText.length > 0)
        }
        onAccepted: {
            if (!BBackend.keyManager.generateMasterKey(seedPhraseText, BBackend.debugMode)) {
                let dialog = _applicationManager.messageDialog(qsTr("Wrong seed pharse."))
                dialog.onClosed.connect(_validateDialog.open)
                dialog.open()
            } else {
                _base.autoDestroy()
            }
        }
        onRejected: {
            _generateDialog.open()
        }
    }

    BSeedPhraseDialog {
        id: _restoreDialog
        type: BSeedPhraseDialog.Type.Restore
        readOnly: false

        onSeedPhraseTextChanged: {
            enableAccept = (seedPhraseText.length > 0 && BBackend.keyManager.validateSeed(seedPhraseText))
        }
        onAccepted: {
            BBackend.keyManager.generateMasterKey(seedPhraseText, BBackend.debugMode) // TODO if failed?
            _base.autoDestroy()
        }
        onRejected: {
            _base.open()
        }
    }
}
