import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../api"
import "../js/functions.js" as Funcs



BasePopup{
    id: _base


    ok: false
    acceptText: qsTr("Test")
    rejectText: qsTr("Back")
    closable: false

    signal match()

        TitleText{
            id: _title
            anchors{
                horizontalCenter: parent.horizontalCenter
                top: parent.top
                topMargin: 20
            }
            text: qsTr("Test yourself wheather you kept your phrase in mind.")
            wrapMode: Text.WordWrap
            sub: true
        }
        /*
        Text{
            id: _sub_title
            anchors{
                horizontalCenter: parent.horizontalCenter
                top: _title.bottom
                topMargin: 10
            }
            text: qsTr("Input your phrase again")
            font{
                pixelSize: 12
            }
            wrapMode: Text.WordWrap
            color: palette.mid
        }
        */

        TextArea{
            id: _mnemo_text
            anchors{
                left: parent.left
                right: parent.right
                bottom: parent.bottom
                top: _title.bottom
                margins: 20
            }
            font{
                pixelSize: 14
            }
            wrapMode: Text.WordWrap
            placeholderText: qsTr("Input again your phrase here")
            placeholderTextColor: palette.mid
            color: palette.text
            leftPadding: 20
            rightPadding: 20
            cursorVisible: true
            background: Rectangle{
//                radius: 10
                color: "transparent"
                XemLine{
                    anchors{
                        top: parent.top
                    }
                    width: parent.width
                }
                XemLine{
                    anchors{
                        bottom: parent.bottom
                    }
                    width: parent.width
                }
            }
        }

        onAccept: {
                    if( CoinApi.keyMan.generateMasterKey(_mnemo_text.text, CoinApi.debug)){
                        match()
                    }else{
                        _mnemo_text.clear()
                    }
        }

        onReject: {
            close()
        }

        onOpened: {
            _mnemo_text.clear()
        }
}
