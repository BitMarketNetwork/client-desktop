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
            model: BBackend.settingsManager.languageList
            textRole: "friendlyName"
            valueRole: "name"
            enabled: false
            onModelChanged: {
                currentIndex = BBackend.settingsManager.currentLanguageIndex()
            }
            onActivated: {
                BBackend.settingsManager.currentLanguageName = model[index]['name']
                currentIndex = BBackend.settingsManager.currentLanguageIndex()
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
