
import QtQuick 2.12
import "../controls"


BasePopup{

    property alias text: _message.text

        Text{
            id: _message
            width: 500
            lineHeight : 2.
            anchors{
//                horizontalCenter: parent.horizontalCenter
                top:parent.top
                topMargin: 40
                left: parent.left
                leftMargin: 40

            }

            color: palette.text
            wrapMode: Text.Wrap
            antialiasing: true
            horizontalAlignment: Text.AlignLeft
            elide: Text.ElideRight
            font{
                family: "Arial"
                pixelSize: 14
            }

        }
}
