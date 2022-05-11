import QtQuick
import QtQuick.Controls.Material
import "../application"
import "../basiccontrols"

BPane {
    id: _base
    property string title: qsTr("Application")
    property string iconPath: _applicationManager.imagePath("icon-info.svg")

    contentItem: BDialogScrollableLayout {
        BLogoImage {
            BLayout.columnSpan: parent.columns
            BLayout.minimumWidth: implicitWidth
            BLayout.alignment: Qt.AlignTop | Qt.AlignHCenter
            huge: true
        }

        BDialogSeparator {
            BLayout.minimumWidth: _applicationStyle.dialogInputWidth
            transparent: true
        }

        BInfoLayout {
            BLayout.columnSpan: parent.columns
            BLayout.fillWidth: true

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
            BLayout.columnSpan: parent.columns
            BLayout.minimumWidth: implicitWidth
            BLayout.alignment: Qt.AlignBottom | Qt.AlignHCenter

            font.bold: true
            // TODO year from compile time
            text: qsTr("Copyright © 2020-2022 %1.\nAll rights reserved.").arg(Qt.application.organization)
            horizontalAlignment: BLabel.AlignHCenter
        }
    }
}
