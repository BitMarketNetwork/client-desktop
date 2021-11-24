import QtQuick
import QtQuick.Controls

ToolButton {
    id: _base
    property FontMetrics fontMetrics: FontMetrics { font: _base.font }

    // ICON {
    icon.width: _applicationStyle.icon.normalWidth
    icon.height: _applicationStyle.icon.normalHeight
    spacing: fontMetrics.averageCharacterWidth // BIconLabel comportable
    // } ICON
}
