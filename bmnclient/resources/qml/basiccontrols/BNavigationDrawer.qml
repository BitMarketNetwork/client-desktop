import QtQuick 2.15
import QtQuick.Controls.Material 2.15

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
