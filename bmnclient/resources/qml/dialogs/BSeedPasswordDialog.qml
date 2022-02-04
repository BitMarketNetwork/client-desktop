import QtQuick.Controls.Material
import "../application"
import "../basiccontrols"

BDialog {
    id: _base
    signal passwordAccepted(string password)
    property var strength: BBackend.password.calcStrength("")

    title: qsTr("Set up seed's password (optional)")
    contentItem: BDialogLayout {
        columns: 3

        BDialogPromptLabel {
            text: qsTr("New password:")
        }
        BDialogInputTextField {
            id: _password1
            echoMode: _showPassword.checked ? BTextField.Normal : BTextField.Password
            placeholderText: qsTr("Enter your password")
            onTextChanged: {
                updatePasswordState()
            }

        }
        BDialogValidLabel {
            id: _strength
            maxAdvancedTextLength: BBackend.password.maxStrengthNameLength
            advancedText: _base.strength["name"]
            status: _base.strength["status"]
        }

        BDialogPromptLabel {
            text: qsTr("New password confirmation:")
        }
        BDialogInputTextField {
            id: _password2
            echoMode: _showPassword.checked ? BTextField.Normal : BTextField.Password
            placeholderText: qsTr("Repeat your password here")
            onTextChanged: {
                updatePasswordState()
            }

        }
        BDialogValidLabel {
            id: _confirmed
            maxAdvancedTextLength: _strength.maxAdvancedTextLength
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
            id: _continueButton
            BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
            text: BCommon.button.createRole
            enabled: false
        }

        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.RejectRole
            text: BCommon.button.continueRole
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
        _password2.clear()
        _showPassword.checked = false
    }

    function updatePasswordState() {
        if (_password1.text === _password2.text) {
            _continueButton.enabled = true
        } else {
            _continueButton.enabled = false
        }
    }

}
