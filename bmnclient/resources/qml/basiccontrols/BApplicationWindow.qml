import QtQuick.Controls 2.15
import QtQuick.Window 2.15
import QtQuick.Controls.Material 2.15

ApplicationWindow {
    // https://en.wikipedia.org/wiki/16:9_aspect_ratio
    // HD
    minimumWidth: Math.min(Screen.desktopAvailableWidth, 1280) // TODO DPI
    minimumHeight: Math.min(Screen.desktopAvailableHeight, 720) // TODO DPI
    width: minimumWidth
    height: minimumHeight

    // https://doc.qt.io/qt-5/qtquickcontrols2-material.html
    Material.theme: _applicationStyle.currentTheme["theme"]
    Material.primary: _applicationStyle.currentTheme["primary"]
    Material.accent: _applicationStyle.currentTheme["accent"]

    locale: _applicationStyle.currentLocale

    onSceneGraphError: {
        console.error("QML rendering error ${error}: ${message}") // TODO
    }
}
