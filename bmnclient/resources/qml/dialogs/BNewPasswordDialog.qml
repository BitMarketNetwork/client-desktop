import QtQuick.Controls.Material 2.15
import "../application"
import "../basiccontrols"

BDialog {
    id: _base

    signal passwordAccepted(string password)
    signal passwordReady

    title: qsTr("Set up new password")
    contentItem: BDialogLayout {
        columns: 3

        BDialogPromtLabel {
            text: qsTr("New password:")
        }
        BDialogInputTextField {
            id: _password1
            echoMode: _showPassword.checked ? BTextField.Normal : BTextField.Password
            placeholderText: qsTr("Enter your password")
            onTextChanged: {
                let index = BPasswordStrength.getIndex(text)
                _strength.advancedText = BPasswordStrength.getString(index)
                _strength.status = BPasswordStrength.getValidMode(index)
                updatePasswordState()
            }
        }
        BDialogValidLabel {
            id: _strength
            maxAdvancedTextLength: BPasswordStrength.getMaxStringLength()
        }

        BDialogPromtLabel {
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

        BDialogPromtLabel {
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
            id: _acceptButton
            BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
            text: BStandardText.button.okRole
            enabled: false
        }
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.RejectRole
            text: BStandardText.button.cancelRole
        }
    }

    onAboutToShow: {
        onReset()
        _password1.forceActiveFocus()
    }
    onAccepted: {
        if (!_acceptButton.enabled) {
            console.assert(_acceptButton.enabled)
            open()
            return
        }
        passwordAccepted(_password1.text)
    }
    onReset: {
        _password1.clear()
        _password2.clear()
        _showPassword.checked = false
    }

    function updatePasswordState() {
        if (_password1.text.length > 0 && _password1.text === _password2.text) {
            _confirmed.status = BDialogValidLabel.Status.Accept
            _acceptButton.enabled = BPasswordStrength.isAcceptable(BPasswordStrength.getIndex(_password1.text))
        } else {
            if (_password1.text.length === 0 && _password2.text.length === 0) {
                _confirmed.status = BDialogValidLabel.Status.Unset
            } else {
                _confirmed.status = BDialogValidLabel.Status.Reject
            }
            _acceptButton.enabled = false
        }
    }
}
