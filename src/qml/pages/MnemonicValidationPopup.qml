import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../api"
import "../js/functions.js" as Funcs



BasePopup{
    id: _base


    ok: false
    acceptText: qsTr("Test","Master key window")
    rejectText: qsTr("Back","Master key window")
    closable: false

    signal match()

        TitleText{
            id: _title
            anchors{
                horizontalCenter: parent.horizontalCenter
                top: parent.top
                topMargin: 20
            }
            text: qsTr("Test yourself whether you memorized the phrase","Master key window")
            wrapMode: Text.WordWrap
            sub: true
        }

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
            placeholderText: qsTr("Re-enter your phrase","Master key window")
            placeholderTextColor: palette.mid
            color: palette.text
            leftPadding: 20
            rightPadding: 20
            cursorVisible: true
            background: Base{
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
                    if( CoinApi.keyMan.generateMasterKey(_mnemo_text.text, CoinApi.debugSeed)){
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
