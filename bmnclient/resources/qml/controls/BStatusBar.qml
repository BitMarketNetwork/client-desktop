import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Material

import "../basiccontrols"

BPane {
    id: _base

    property var isSync: BBackend.statusBar.isSync
    property var display

    contentItem: BRowLayout {
        anchors.fill: parent

        /* TODO
        BIconLabel {
            Layout.alignment: Qt.AlignLeft
            Layout.leftMargin: 5
            icon.width: _applicationStyle.icon.smallWidth
            icon.height: _applicationStyle.icon.smallHeight
            icon.source: _applicationManager.imagePath("check-solid.svg")
            text: qsTr("Connected")
        }*/
        BRowLayout {
            spacing: 5
            BIconImage {
                id: _rotateImage
                sourceSize.width: _applicationStyle.icon.smallWidth
                sourceSize.height: _applicationStyle.icon.smallHeight
                Layout.leftMargin: 5
                visible: isSync
                color: Material.theme === Material.Dark ? Material.foreground : "transparent"
                source: _applicationManager.imagePath("rotate-solid.svg")

                RotationAnimator {
                    id: _rotationAnimation
                    target: _rotateImage
                    from: 0
                    to: 360
                    duration: _applicationStyle.animation.rotationDuration
                    running: isSync
                    loops: Animation.Infinite
                }
            }
            BIconImage {
                sourceSize.width: _applicationStyle.icon.smallWidth
                sourceSize.height: _applicationStyle.icon.smallHeight
                Layout.leftMargin: 5
                visible: !isSync
                color: Material.theme === Material.Dark ? Material.foreground : "transparent"
                source: _applicationManager.imagePath("check-solid.svg")
            }
            BLabel {
                Layout.fillWidth: true
                visible: display === BItemDelegate.TextBesideIcon
                text: isSync ? qsTr("Synchronization") : qsTr("Synchronized")
            }
        }
    }
}
