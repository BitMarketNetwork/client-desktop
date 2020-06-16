import QtQuick 2.12
import QtQuick.Controls 2.12
import "../api"


Rectangle {
    id: _base

    property alias textStatic: _text_static.text
    property alias readOnly: _text_static.readOnly
    property alias placeholder: _text_static.placeholderText

    color: palette.base



    function clear(){
        _text_static.clear()
    }


        TextArea{
            id: _text_static
            focus: true
            anchors{
                top: parent.top
                left: parent.left
                right: parent.right
                margins: 20
            }
            font{
                pixelSize: 16
                family: "Arial"
            }
            wrapMode: Text.WordWrap
            cursorVisible: true
            selectByMouse: CoinApi.debugSeed
            height: 100

            background: Rectangle{
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

        Component.onCompleted: {
        }


}
