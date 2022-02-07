import QtQuick.Controls.Material
import "../application"
import "../basiccontrols"

BDialog {
    id: _base
    signal passwordAccepted(string password)

    title: qsTr("Set up seed's password (optional)")
    contentItem: BDialogLayout {
        columns: 2

        BDialogPromptLabel {
            text: qsTr("Seed's password:")
        }
        BDialogInputTextField {
            id: _password1
            echoMode: _showPassword.checked ? BTextField.Normal : BTextField.Password
            placeholderText: qsTr("Enter your password")
        }

        BDialogPromptLabel {
            text: qsTr("Show password:")
        }

        BDialogInputSwitch {
            id: _showPassword
            BLayout.columnSpan: parent.columns - 1
        }

        // TODO show password rules
    }

    footer: BDialogButtonBox {
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
            text: BCommon.button.continueRole
            enabled: true
        }
    }

    onAboutToShow: {
        onReset()
        _password1.forceActiveFocus(Qt.TabFocus)
    }
    onAccepted: {
        passwordAccepted(_password1.text)
    }
    onReset: {
        _password1.clear()
        _showPassword.checked = true
    }


}
