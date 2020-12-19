import QtQuick 2.15
import QtQuick.Controls.Material 2.15

BLabel {
    id: _base
    property bool transparent: false
    background: Rectangle {
        y: _base.height / 2 - _applicationStyle.dividerSize / 2
        implicitHeight: _applicationStyle.dividerSize
        color: _base.transparent ? "transparent" : Material.dividerColor
    }
}
