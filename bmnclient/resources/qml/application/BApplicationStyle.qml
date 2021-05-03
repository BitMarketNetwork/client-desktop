import QtQuick 2.15
import QtQuick.Controls.Material 2.15
import "../basiccontrols"

QtObject {
    required property BApplicationWindow applicationWindow

    ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    // Theme
    ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    readonly property variant themeList: [{
            "name": "light",
            "friendlyName": qsTr("Light (Default)"),
            "theme": Material.Light,
            "primary": Material.BlueGrey,
            "accent": Material.Blue
        }, {
            "name": "dark",
            "friendlyName": qsTr("Dark"),
            "theme": Material.Dark,
            "primary": Material.BlueGrey,
            "accent": Material.Blue
        }]
    readonly property int currentThemeIndex: {
        let name = BBackend.settingsManager.currentThemeName
        for (let i in themeList) {
            if (themeList[i].name === name) {
                return i
            }
        }
        return 0
    }
    readonly property var currentTheme: themeList[currentThemeIndex]

    ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    property FontMetrics baseFontMetrics: FontMetrics {
        font: applicationWindow.font
    }

    property QtObject fontPointSizeFactor: QtObject {
        property real small: 0.8
        property real normal: 1.0
        property real large: 1.2
        property real huge: 1.4
    }

    property QtObject icon: QtObject {
        property int normalWidth: 24
        property int normalHeight: 24
        property int largeWidth: 48
        property int largeHeight: 48
    }

    property real backgroundDarkFactor: applicationWindow.Material.theme === Material.Dark ? 1.2 : 1.04 // TODO to themeList
    property real padding: baseFontMetrics.height
    property real spacing: baseFontMetrics.height * 0.5
    property real dividerSize: 1

    property int dialogDescriptionAlignment: Qt.AlignVCenter | Qt.AlignLeft
    property int dialogPromptAlignment: Qt.AlignVCenter | Qt.AlignRight
    property int dialogInputAlignment: Qt.AlignVCenter | Qt.AlignLeft
    property int dialogInputWidth: baseFontMetrics.averageCharacterWidth * 70
    property int dialogColumnSpacing: baseFontMetrics.averageCharacterWidth
    property int dialogRowSpacing: baseFontMetrics.height * 0.5

    property int infoLabelAlignment: Qt.AlignVCenter | Qt.AlignLeft
    property int infoValueAlignment: Qt.AlignVCenter | Qt.AlignLeft
    property int infoColumnSpacing: 0
    property int infoRowSpacing: 0

    property int animationDuration: 400
    property int tooTipDelay: 400
}
