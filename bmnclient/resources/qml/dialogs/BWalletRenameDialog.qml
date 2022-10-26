import "../application"
import "../basiccontrols"

BDialog {
    id: _base
    title: qsTr("Input new wallet name")
    signal nameChanged(string name)

    contentItem: BDialogLayout {
        BDialogPromptLabel {
            text: qsTr("Wallet Name")
        }

        BDialogInputTextField {
            id: _name
            text: _base.context.name
            placeholderText: qsTr("Enter new wallet name")
            validator: BBackend.keyStore.nameValidator

            onTextChanged: {
                _base.nameChanged(_name.text)
            }
        }
    }

    footer: BDialogButtonBox {
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
            text: BCommon.button.okRole
            enabled: _name.length > 0
        }
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.RejectRole
            text: BCommon.button.cancelRole
        }
    }
}
