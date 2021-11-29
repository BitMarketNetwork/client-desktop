import QtQuick
import QtQuick.Controls.Material

BControl {
    default property alias children: _layout.children

    contentItem: BColumnLayout {
        BRowLayout {
            id: _layout
        }
        Rectangle {
            BLayout.fillWidth: true
            implicitHeight: _applicationStyle.dividerSize
            color: Material.dividerColor
        }
    }
}
