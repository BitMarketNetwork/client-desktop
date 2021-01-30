import QtQuick.Controls.Material 2.15
import "../basiccontrols"

BPane {
    id: _base
    property var coin // CoinListModel item
    property string title: coin.fullName
    property string iconPath: _applicationManager.imagePath(coin.iconPath)

    contentItem: BDialogScrollableLayout {
        BLayout.maximumWidth: -1
        BLogoImage {
            BLayout.columnSpan: parent.columns
            BLayout.minimumWidth: implicitWidth
            BLayout.alignment: Qt.AlignTop | Qt.AlignHCenter
            huge: true
            source: _base.iconPath
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
                text: _base.coin.fullName
            }
            BInfoSeparator {}

            BInfoLabel {
                text: qsTr("Short name:")
            }
            BInfoValue {
                text: _base.coin.shortName
            }
            BInfoSeparator {}

            BInfoLabel {
                text: qsTr("Daemon status:")
            }
            BInfoValue {
                text: _base.coin.remoteState.status > 0 ? "Online" : "Offline"
                color: Material.color(_base.coin.remoteState.status > 0 ? Material.Green : Material.Red)
            }
            BInfoSeparator {}

            BInfoLabel {
                text: qsTr("Daemon version:")
            }
            BInfoValue {
                text: "\"%1\" (%2)".arg(_base.coin.remoteState.humanVersion).arg(_base.coin.remoteState.version)
            }
            BInfoSeparator {}

            BInfoLabel {
                text: qsTr("Daemon height:")
            }
            BInfoValue {
                text: _applicationManager.integerToLocaleString(_base.coin.remoteState.height)
            }
            BInfoSeparator {}
        }
    }
}
