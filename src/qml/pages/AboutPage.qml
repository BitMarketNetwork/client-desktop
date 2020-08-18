import QtQuick 2.12
import QtQuick.Controls 2.12
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
        margins: 10
//        horizontalCenter: parent.horizontalCenter
        left: parent.left
        leftMargin: 20
      }
      text: qsTr("About","About program window")
    }
    Flickable{
        id: _body
        anchors{
//            bottom: _btn.top
            top: _title.bottom
            right: parent.right
            left: parent.left
            margins: 10
            rightMargin: parent.width * rightSpaceFactor
        }
        height: 380
        contentHeight: 380
        clip: true
        ScrollBar.vertical: ScrollBar{
            width: 30
//            policy: ScrollBar.AlwaysOn
        }

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
                name: qsTr("Application name:","About program window")
                value: Qt.application.name
            }
            AboutLabel{
                name: qsTr("Server version:","About program window")
                value: CoinApi.ui.serverVersion
            }
            AboutLabel{
                name: qsTr("Client version:","About program window")
                value: Qt.application.version 
            }
        }
            CoinInfoTabView{
                id: _coin_info

                anchors{
                    top: _basic_info.bottom
                    left: parent.left
//                    horizontalCenter: parent.horizontalCenter
                    right: parent.right
                    topMargin: 5

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
        TitleText{
            id: _company_name
            anchors{
                left: parent.left
                bottom: parent.bottom
                margins: 10
            }
            text: Qt.application.organization
            color: palette.mid
            sub: true
            visible: false
        }
        TitleText{
            anchors{
                right: parent.right
                bottom: parent.bottom
                margins: 10
            }
            text: qsTr("All right reserved @ 2020","About program window")
            color: palette.mid
            sub: true
        }
        BigBlueButton{
            id: _btn
            anchors{
                left: _body.left
                right: _body.right
//                top: _body.bottom
//                topMargin: 20
//                horizontalCenter: _body.horizontalCenter
                bottom: parent.bottom
                bottomMargin: 10
                margins: 20
            }
            text: qsTr("Close")
//            width: 200
            onClicked: {
                popPage();
            }
        }
}
