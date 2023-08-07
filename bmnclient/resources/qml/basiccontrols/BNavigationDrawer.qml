import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

BControl {
    default property alias children: _layout.children

    contentItem: BColumnLayout {
        BRowLayout {
            id: _layout
        }
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: _applicationStyle.dividerSize
            color: Material.dividerColor
        }
    }
}
