import QtQuick
import QtQuick.Controls.Material
import "../basiccontrols"

BPane {
    id: _base

    contentItem: BRowLayout {
        anchors.fill: parent
        spacing: 5

        BIconLabel {
            BLayout.alignment: Qt.AlignLeft
            BLayout.leftMargin: 5
            icon.width: _applicationStyle.icon.smallWidth
            icon.height: _applicationStyle.icon.smallHeight
            icon.source: _applicationManager.imagePath("check-solid.svg")
            text: qsTr("Connected")
        }
        BIconLabel {
            BLayout.alignment: Qt.AlignRight
            BLayout.rightMargin: 5
            icon.width: _applicationStyle.icon.smallWidth
            icon.height: _applicationStyle.icon.smallHeight
            icon.source: _applicationManager.imagePath("rotate-solid.svg")
            text: qsTr("Synchronization")
        }
    }
}
