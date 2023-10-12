import QtQuick
import QtQuick.Controls

import "../basiccontrols"

MenuItem {
    id: _base
    property FontMetrics fontMetrics: FontMetrics { font: _base.font }

    // ICON {
    icon.width: _applicationStyle.icon.normalWidth
    icon.height: _applicationStyle.icon.normalHeight
    spacing: fontMetrics.averageCharacterWidth // BIconLabel comportable
    // } ICON

    indicator: BIconImage {
        x: _base.leftPadding
        y: parent.height / 2 - height / 2
        sourceSize.width: _applicationStyle.icon.smallWidth
        sourceSize.height: _applicationStyle.icon.smallHeight
        visible: _base.checked
        color: Material.theme === Material.Dark ? Material.foreground : "transparent"
        source: _applicationManager.imagePath("check-solid.svg")
    }
}
