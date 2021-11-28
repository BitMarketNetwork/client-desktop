import QtQuick
import QtQuick.Controls.Material

BLabel {
    id: _base
    property bool transparent: false
    background: Item {
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            implicitHeight: _applicationStyle.dividerSize
            color: _base.transparent ? "transparent" : Material.dividerColor
        }
    }
}
