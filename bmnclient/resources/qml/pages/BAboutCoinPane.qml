import QtQuick.Controls.Material 2.15
import "../basiccontrols"

BPane {
    id: _base
    property string title: object.coin.fullName
    property string iconSource: _applicationManager.coinImageSource(object.coin.shortName)

    contentItem: BDialogScrollableLayout {
        BLayout.maximumWidth: -1
        BLogoImage {
            BLayout.columnSpan: parent.columns
            BLayout.minimumWidth: implicitWidth
            BLayout.alignment: Qt.AlignTop | Qt.AlignHCenter
            huge: true
            source: _base.iconSource
        }

        BDialogSeparator {
            BLayout.minimumWidth: _applicationStyle.dialogInputWidth
            transparent: true
        }

        BInfoLayout {
            BLayout.columnSpan: parent.columns
            BLayout.fillWidth: true

            BInfoLabel {
                text: qsTr("Full name:")
            }
            BInfoValue {
                text: object.coin.fullName
            }
            BInfoSeparator {}

            BInfoLabel {
                text: qsTr("Short name:")
            }
            BInfoValue {
                text: object.coin.shortName
            }
            BInfoSeparator {}

            BInfoLabel {
                text: qsTr("Daemon status:")
            }
            BInfoValue {
                text: object.status > 0 ? "Online" : "Offline"
                color: Material.color(object.status > 0 ? Material.Green : Material.Red)
            }
            BInfoSeparator {}

            BInfoLabel {
                text: qsTr("Daemon version:")
            }
            BInfoValue {
                text: "\"%1\" (%2)".arg(object.versionString).arg(object.version)
            }
            BInfoSeparator {}

            BInfoLabel {
                text: qsTr("Daemon height:")
            }
            BInfoValue {
                text: _applicationManager.integerToLocaleString(object.height)
            }
            BInfoSeparator {}
        }
    }
}
