import QtQuick 2.12
import QtQuick.Controls 2.12

import "../js/constants.js" as Const


Base {

    property alias name:    _name.text
    property alias value:   _value.text
    property alias unit:    _unit.text
    property alias placeholder: _value.placeholderText
    property alias nameTextSize: _name.font.pixelSize
    property alias valueTextSize: _value.font.pixelSize
    property alias color: _name.color
    property alias valueColor: _value.color
    property alias echoMode: _value.echoMode
    property alias labelWidth: _name.width

    height: 30
    width: parent.width

    LabelText{
        id: _name
        anchors{
            left: parent.left
//            leftMargin: defMargin
            verticalCenter: parent.verticalCenter
        }
    }
    TextField{
        id: _value
        anchors{
            verticalCenter: parent.verticalCenter
            left: _name.right
            right: parent.right
//            leftMargin: 250
        }
//        x: 400
//        width: parent.width * 0.5
        color: palette.text
        readOnly: true
        selectByMouse: true
        font{
            pixelSize: 10
            family: "Arial"
        }
        leftPadding: 10
        rightPadding: 10
        horizontalAlignment: TextInput.AlignLeft
        verticalAlignment: TextInput.AlignVCenter
        maximumLength: 70

        background: Rectangle{
//            implicitWidth: _value.width
            color: _value.enabled ? "transparent" : "#353637"
            XemLine{
                id: _top_line
                anchors{
                    top:parent.top
                }
                width: _value.width
                visible: false
            }
            XemLine{
                id: _bottom_line
                anchors{
                    bottom:parent.bottom
                }
                width: _value.width
                blue: false
            }
        }
    }


    LabelText{
        id: _unit
        anchors{
            right: parent.right
            rightMargin: 10
            verticalCenter: parent.verticalCenter

        }
    }
    /*
    Rectangle{
        anchors{
            // right: parent.right
            right: parent.right
            rightMargin: 10
            left: _name.right
            leftMargin: 10
            bottom: parent.bottom
        }
        color: _name.color
        height: 1
    }
    */
}
