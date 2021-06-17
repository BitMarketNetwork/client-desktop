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
            model: BBackend.settings.language.translationList
            textRole: "friendlyName"
            valueRole: "name"
            Component.onCompleted: {
                currentIndex = indexOfValue(BBackend.settings.language.currentName)
            }
            onActivated: {
                BBackend.settings.language.currentName = currentValue
                currentIndex = indexOfValue(BBackend.settings.language.currentName)
            }
        }

        BDialogPromptLabel {
            text: qsTr("Theme:")
        }
        BDialogInputComboBox {
            model: _applicationStyle.themeList
            textRole: "friendlyName"
            valueRole: "name"
            onModelChanged: {
                currentIndex = _applicationStyle.currentThemeIndex
            }
            onActivated: {
                BBackend.settings.theme.currentName = model[index]['name']
                currentIndex = _applicationStyle.currentThemeIndex
            }
        }
    }
}
