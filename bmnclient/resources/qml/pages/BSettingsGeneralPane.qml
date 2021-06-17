import QtQuick 2.15
import "../application"
import "../basiccontrols"

BPane {
    property string title: qsTr("General")
    property string iconPath: _applicationManager.imagePath("icon-cog.svg")

    contentItem: BDialogScrollableLayout {
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
}
