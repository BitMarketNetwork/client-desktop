import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Material

import "../application"
import "../basiccontrols"
import "../dialogcontrols"

BPane {
    id: _base
    property string title: qsTr("Application")
    property string iconPath: _applicationManager.imagePath("icon-info.svg")

    contentItem: BDialogScrollableLayout {
        BLogoImage {
            Layout.columnSpan: parent.columns
            Layout.minimumWidth: implicitWidth
            Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
            huge: true
        }

        BDialogSeparator {
            Layout.minimumWidth: _applicationStyle.dialogInputWidth
            transparent: true
        }

        BInfoLayout {
            Layout.columnSpan: parent.columns
            Layout.fillWidth: true

            BInfoLabel {
                text: qsTr("Application name:")
            }
            BInfoValue {
                text: Qt.application.name
            }
            BInfoSeparator {}

            BInfoLabel {
                text: qsTr("Application version:")
            }
            BInfoValue {
                text: Qt.application.version
            }

            BInfoSeparator {}

            BInfoLabel {
                text: qsTr("Application update:")
            }

            BInfoValue {
                id: _update
                visible: !BBackend.update.isAvailable
                text: qsTr("Not found")
            }

            BInfoValue {
                id: _updateAvailable
                visible: BBackend.update.isAvailable
                text: qsTr("Version %1 available!").arg(BBackend.update.version)
                color: Material.color(Material.Green)
                MouseArea {
                    id: mouseHyperlinkArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        Qt.openUrlExternally(BBackend.update.url)
                    }
                }
            }

            BInfoSeparator {}
        }

        BDialogSpacer {}
        BLabel {
            Layout.columnSpan: parent.columns
            Layout.minimumWidth: implicitWidth
            Layout.alignment: Qt.AlignBottom | Qt.AlignHCenter

            font.bold: true
            // TODO year from compile time
            text: qsTr("Copyright © 2020-2023 %1.\nAll rights reserved.").arg(Qt.application.organization)
            horizontalAlignment: BLabel.AlignHCenter
        }
    }
}
