import QtQuick 2.15
import QtQuick.Controls.Material 2.15

BControl {
    id: _base
    property bool huge: false
    property real imageWidth: 0 // _applicationStyle.icon.largeWidth
    property real imageHeight: _applicationStyle.icon.largeHeight * (huge ? 2 : 1)
    property string source: _applicationManager.imagePath("logo.svg")

    contentItem: BIconImage {
        id: _image
        source: _base.source
        sourceSize.width: _base.imageWidth
        sourceSize.height: _base.imageHeight
        color: Material.theme === Material.Dark ? Material.foreground : "transparent"
    }
}
