import "../application"
import "../basiccontrols"

BDialog {
    signal generateAccepted
    signal restoreAccepted
    signal restoreBackupAccepted

    title: qsTr("Root Key generation")

    contentItem: BDialogLayout {
        columns: 1

        // TODO advanced welcome text

        BDialogInputRadioButton {
            id: _generateButton
            text: qsTr("Generate new Root Key")
            checked: true
        }
        BDialogInputRadioButton {
            id: _restoreButton
            text: qsTr("Restore Root Key from Seed Phrase")
        }
        BDialogInputRadioButton {
            id: _restoreBackupButton
            text: qsTr("Restore wallet from backup")
            enabled: false
        }
    }

    footer: BDialogButtonBox {
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
            text: BCommon.button.continueRole
        }
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.RejectRole
            text: BCommon.button.cancelRole
        }
    }

    onAccepted: {
        if (_generateButton.checked) {
            generateAccepted()
        } else if (_restoreButton.checked) {
            restoreAccepted()
        } else if (_restoreBackupButton.checked) {
            restoreBackupAccepted()
        }
    }
}
