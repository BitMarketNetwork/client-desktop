import QtQuick 2.12
import "../controls"
import "../widgets"
import "../api"
import "../js/constants.js" as Constants


BasePage {
    id: _base
    readonly property int pageId: Constants.pageId.about

    TitleText{
      id: _title
      anchors{
        top: parent.top
        margins: defaultMargin * 2
//        horizontalCenter: parent.horizontalCenter
        left: parent.left

      }
      text: qsTr("About program")
    }
    Rectangle{
        id: _body
        anchors{
//            bottom: _btn.top
            top: _title.bottom
            right: parent.horizontalCenter
            left: parent.left
            margins: defaultMargin
        }
        height: 400
        color: palette.base
//        color: "blue"
        Column{
            id: _basic_info
            anchors{
                top: parent.top
                left: parent.left
                right: parent.right
//                right: parent.horizontalCenter
//                margins: defaultMargin
//                topMargin: 20
            }
//            spacing: 10

            AboutLabel{
                name: qsTr("Application name:")
                value: Qt.application.name
            }
            AboutLabel{
                name: qsTr("Server version:")
                value: CoinApi.ui.serverVersion
            }
            AboutLabel{
                name: qsTr("Client version:")
                value: Qt.application.version 
            }
        }
            CoinInfoTabView{
                id: _coin_info

                anchors{
                    top: _basic_info.bottom
                    left: parent.left
//                    right: parent.horizontalCenter
                    right: parent.right
                    topMargin: defaultMargin

                }

//                width: parent.width - 20
                nameModel: CoinApi.ui.coinInfoModel

                coinName: CoinApi.ui.coinDaemon.name
                coinVersionHuman: CoinApi.ui.coinDaemon.versionHuman
                coinVersionNum: CoinApi.ui.coinDaemon.versionNum
                coinHeight: CoinApi.ui.coinDaemon.height
                coinOnline: CoinApi.ui.coinDaemon.online

                onSelectCoin: {
                    CoinApi.ui.coinDaemonIndex = index
                }
            }

    }
        BigBlueButton{
            id: _btn
            anchors{
                left: _body.left
                right: _body.right
                top: _body.bottom
                topMargin: 20
            }
            text: qsTr("Close")
            onClicked: {
                popPage();
            }
        }
        TitleText{
            id: _company_name
            anchors{
                left: parent.left
                bottom: parent.bottom
                margins: defaultMargin
            }
            text: Qt.application.organization
            color: palette.mid
            sub: true
        }
        TitleText{
            anchors{
                right: parent.right
                bottom: parent.bottom
                margins: defaultMargin
            }
            text: qsTr("All right reserved @2020")
            color: palette.mid
            sub: true
        }

        Component.onCompleted: {
                console.log( `coin names: ${CoinApi.ui.coinInfoModel}`);
        }
}
