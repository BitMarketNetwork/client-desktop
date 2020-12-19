import QtQuick 2.15
import QtQuick.Controls 2.15

RadioButton {
    id: _base
    property FontMetrics fontMetrics: FontMetrics { font: _base.font }

    // ICON {
    icon.width: _applicationStyle.icon.normalWidth
    icon.height: _applicationStyle.icon.normalHeight
    spacing: fontMetrics.averageCharacterWidth // BIconLabel comportable
    // } ICON
}
