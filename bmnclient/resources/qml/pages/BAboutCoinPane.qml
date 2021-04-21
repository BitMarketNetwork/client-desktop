import QtQuick.Controls.Material 2.15
import "../basiccontrols"

BPane {
    id: _base
    property var coin // CoinModel
    property string title: coin.fullName
    property string iconPath: _applicationManager.imagePath(coin.iconPath)

    contentItem: BDialogScrollableLayout {
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

            BInfoSeparator {
                transparent: true
            }

            BInfoLabel {
                text: qsTr("Server URL:")
            }
            BInfoValue {
                text: _base.coin.serverData.serverUrl
            }
            BInfoSeparator {}

            BInfoLabel {
                text: qsTr("Server name:")
            }
            BInfoValue {
                text: _base.coin.serverData.serverName
            }
            BInfoSeparator {}

            BInfoLabel {
                text: qsTr("Server version:")
            }
            BInfoValue {
                text: "%1 (%2)".arg(_base.coin.serverData.serverVersionHuman).arg(_base.coin.serverData.serverVersionHex)
            }
            BInfoSeparator {}

            BInfoSeparator {
                transparent: true
            }

            BInfoLabel {

                text: qsTr("Daemon status:")
            }
            BInfoValue {
                text: _base.coin.serverData.status > 0 ? "Online" : "Offline"
                color: Material.color(_base.coin.serverData.status > 0 ? Material.Green : Material.Red)
            }
            BInfoSeparator {}

            BInfoLabel {
                text: qsTr("Daemon version:")
            }
            BInfoValue {
                text: "%1 (%2)".arg(_base.coin.serverData.versionHuman).arg(_base.coin.serverData.versionHex)
            }
            BInfoSeparator {}

            BInfoLabel {
                text: qsTr("Daemon height:")
            }
            BInfoValue {
                text: _base.coin.serverData.heightHuman
            }
            BInfoSeparator {}
        }
    }
}
