import "../application"
import "../basiccontrols"

BDialog {
    id: _base
    default property alias content: _layout.children

    signal passwordAccepted(string password)
    signal passwordReady

    title: qsTr("Input password")
    contentItem: BDialogLayout {
        id: _layout

        BDialogPromtLabel {
            text: qsTr("Password:")
        }
        BDialogInputTextField {
            id: _password1
            echoMode: _showPassword.checked ? BTextField.Normal : BTextField.Password
            placeholderText: qsTr("Enter your password")
        }

        BDialogPromtLabel {
            text: qsTr("Show password:")
        }
        BDialogInputSwitch {
            id: _showPassword
        }
    }
    footer: BDialogButtonBox {
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
            text: BStandardText.buttonText.okRole
            enabled: _password1.text.length > 0
        }
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.RejectRole
            text: BStandardText.buttonText.cancelRole
        }
    }

    onAboutToShow: {
        onReset()
        _password1.forceActiveFocus()
    }
    onAccepted: {
        passwordAccepted(_password1.text)
    }
    onReset: {
        _password1.clear()
        _showPassword.checked = false
    }
}
