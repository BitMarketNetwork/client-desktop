import QtQuick.Controls 2.15
import QtQuick.Window 2.15
import QtQuick.Controls.Material 2.15
import "../application"

ApplicationWindow {
    // https://en.wikipedia.org/wiki/16:9_aspect_ratio
    // qHD
    minimumWidth: Math.min(Screen.desktopAvailableWidth, 960) // TODO DPI
    minimumHeight: Math.min(Screen.desktopAvailableHeight, 540) // TODO DPI
    // HD
    width: Math.min(Screen.desktopAvailableWidth, 1280)
    height: Math.min(Screen.desktopAvailableHeight, 720)

    //x: Math.round((Screen.desktopAvailableWidth - width) / 2)
    //y: Math.round((Screen.desktopAvailableHeight - height) / 2)

    // https://doc.qt.io/qt-5/qtquickcontrols2-material.html
    Material.theme: _applicationStyle.currentTheme["theme"]
    Material.primary: _applicationStyle.currentTheme["primary"]
    Material.accent: _applicationStyle.currentTheme["accent"]

    locale: Qt.locale(BBackend.settingsManager.currentLanguageName)
    font: Qt.font(BBackend.settingsManager.font)

    onSceneGraphError: {
        console.error("QML rendering error ${error}: ${message}") // TODO
    }
}
