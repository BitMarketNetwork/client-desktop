import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Material

import "../basiccontrols"

BPane {
    id: _base

    contentItem: BRowLayout {
        anchors.fill: parent
        spacing: 5

        /* TODO
        BIconLabel {
            Layout.alignment: Qt.AlignLeft
            Layout.leftMargin: 5
            icon.width: _applicationStyle.icon.smallWidth
            icon.height: _applicationStyle.icon.smallHeight
            icon.source: _applicationManager.imagePath("check-solid.svg")
            text: qsTr("Connected")
        }*/
        BIconLabel {
            Layout.alignment: Qt.AlignLeft
            Layout.leftMargin: 5
            icon.width: _applicationStyle.icon.smallWidth
            icon.height: _applicationStyle.icon.smallHeight
            icon.source: _applicationManager.imagePath("rotate-solid.svg")
            text: qsTr("Synchronization")
        }
    }
}
