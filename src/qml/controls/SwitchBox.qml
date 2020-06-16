import QtQuick 2.0
import QtQuick.Controls 2.12

Base {

    property alias text: _text.text
    property alias checked: _switch.checked
    property alias nameColor: _text.color

    height: 30

    signal goLink(string link)

        Text{
            anchors{
                left: parent.left
//                margins: 20
                verticalCenter: parent.verticalCenter
            }

            id: _text
            font{
                family: "Arial"
                pixelSize: 14
                bold: checked
            }

            color: palette.mid
//            color: checked? palette.text:palette.mid

            onLinkActivated: { goLink(link) }
        }

        Switch{
            anchors{
//                right: parent.right
//                rightMargin: 20
                left: _text.right
                leftMargin: 10
                verticalCenter: parent.verticalCenter
            }

            id: _switch
            width: 100
            height: 30
         }
}
