import QtQuick
import QtQuick.Controls
import QtQuick.Controls.impl
import QtQuick.Controls.Material

BControl {
    id: _base
    property alias display: _control.display
    property alias icon: _control.icon
    property alias text: _control.text
    property alias color: _control.color
    property FontMetrics fontMetrics: FontMetrics { font: _base.font }

    // ICON {
    icon.width: _applicationStyle.icon.normalWidth
    icon.height: _applicationStyle.icon.normalHeight
    spacing: _base.fontMetrics.averageCharacterWidth // BIconLabel comportable
    // } ICON

    icon.color: enabled ?  Material.foreground : Material.hintTextColor
    color: enabled ?  Material.foreground : Material.hintTextColor

    contentItem: IconLabel {
        id: _control

        leftPadding: 0
        rightPadding: 0
        topPadding: 0
        bottomPadding: 0
        spacing: _base.spacing
        alignment: Qt.AlignVCenter | Qt.AlignLeft

        font: _base.font
    }
}
