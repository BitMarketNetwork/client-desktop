import QtQuick 2.12
import QtQuick.Controls 2.12
import QtGraphicalEffects 1.12
import "../js/functions.js" as Funcs

Rectangle {
    id: _base
    property alias text: _text.text
    property bool checked: false
    height: _text.font.pixelSize * 1.2

    readonly property int iconSize: 20

//    border{
//        width: 1
//    }

    Row{
        anchors{
            fill: parent
        }

        spacing: 10

        Label{
            id: _text
            font{
                pixelSize: 14
                // bold: checked
            }
            color: checked? palette.text: palette.mid
        }

        Image {
            id: _icon
            source: Funcs.loadImage("right-arrow.svg")
            width: iconSize
            height: iconSize
            sourceSize{
                width: iconSize
                height: iconSize
            }
            ColorOverlay  {
                anchors.fill: _icon
                source: _icon
                color: palette.midlight
                visible: !checked
            }
        }
    }

    MouseArea{
        id: _area
        anchors{
            fill: parent
        }
        onClicked: {
            checked = true
        }

        hoverEnabled: true
    }

}
