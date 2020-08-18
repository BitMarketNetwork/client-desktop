import QtQuick 2.0
import QtQuick.Controls 2.12

Base {
    id: _base

    property alias checked: _switch.checked
    property alias nameColor: _text.color
    property string text: ""
    property string offText: ""

    height: 30
//    width: 180

    signal goLink(string link)

        SubText{
            anchors{
                left: parent.left
//                margins: 20
                verticalCenter: parent.verticalCenter
            }

            id: _text
            font{
                bold: checked
            }

            text: _switch.checked || !_base.offText? _base.text: _base.offText
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
