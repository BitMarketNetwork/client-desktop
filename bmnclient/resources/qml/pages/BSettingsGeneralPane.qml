import "../application"
import "../basiccontrols"

BPane {
    property string title: qsTr("General")
    property string iconPath: _applicationManager.imagePath("icon-cog.svg")

    property alias fiatUnityModel: _fiatUnit.model
    property alias currentFiatUnitIndex: _fiatUnit.currentIndex

    contentItem: BDialogScrollableLayout {
        BDialogPromtLabel {
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

        BDialogPromtLabel {
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
                BBackend.settingsManager.currentThemeName = model[index]['name']
                currentIndex = _applicationStyle.currentThemeIndex
            }
        }

        BDialogSeparator {}

        BDialogPromtLabel {
            text: qsTr("Fiat currency:")
        }
        BDialogInputComboBox {
            id: _fiatUnit
            textRole: "name"
        }
    }
}
