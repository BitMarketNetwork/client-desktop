import QtQuick
import QtQuick.Controls.Material
import "../basiccontrols"

QtObject {
    readonly property var themeList: [{
            "name": "light",
            "fullName": qsTr("Light (Default)"),
            "theme": Material.Light,
            "primary": Material.BlueGrey,
            "accent": Material.Blue
        }, {
            "name": "dark",
            "fullName": qsTr("Dark"),
            "theme": Material.Dark,
            "primary": Material.BlueGrey,
            "accent": Material.Blue
        }]
    readonly property var currentTheme: {
        let name = BBackend.settings.theme.currentName
        for (let i in themeList) {
            if (themeList[i].name === name) {
                return themeList[i]
            }
        }
        return themeList[0]
    }

    property FontMetrics baseFontMetrics: FontMetrics {
        font: _applicationWindow.font
    }

    property QtObject fontPointSizeFactor: QtObject {
        property real small: 0.8
        property real normal: 1.0
        property real large: 1.2
        property real huge: 1.4
    }

    property QtObject icon: QtObject {
        property int smallWidth: 12
        property int smallHeight: 12
        property int normalWidth: 24
        property int normalHeight: 24
        property int largeWidth: 48
        property int largeHeight: 48
    }

    property real backgroundDarkFactor: _applicationWindow.Material.theme === Material.Dark ? 1.2 : 1.04 // TODO to themeList
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
