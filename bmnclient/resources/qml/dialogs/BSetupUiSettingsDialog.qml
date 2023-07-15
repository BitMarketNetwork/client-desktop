import "../application"
import "../basiccontrols"
import "../dialogcontrols"

BDialog {
    id: _base
    title: qsTr("Select Language and Theme")

    signal themeAccepted()

    contentItem: BDialogLayout {
        id: _layout

        BDialogPromptLabel {
            text: qsTr("Application language:")
        }
        BDialogInputComboBox {
            stateModel: BBackend.settings.language
        }

        BDialogPromptLabel {
            text: qsTr("Theme:")
        }
        BDialogInputComboBox {
            stateModel: BBackend.settings.theme
            model: _applicationStyle.themeList
        }
    }

    footer: BDialogButtonBox {
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
            text: BCommon.button.okRole
        }
    }

    onAccepted: {
        _base.themeAccepted()
    }
}
