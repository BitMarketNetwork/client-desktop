import QtQuick 2.12
import QtQuick.Controls 2.12

Base {

    id: _base
    property alias name: _name.text
    property alias value: _value.text
    property alias color: _name.color
    property alias bgColor: _bg.color
    property int 	defMargin: 20
    property alias nameFontSize: _name.font.pixelSize
    property alias maxLength: _value.maximumLength
    property alias inputX: _value.x
    property bool  passwordInput: false
    property alias placeHolder: _value.placeholderText
    property alias labelWidth: _name.width
    property alias failure: _underline.red
    property alias valueFontSize: _value.font.pixelSize


    LabelText{
        id: _name
        anchors{
            left: parent.left
                leftMargin: 0
            //bottom: parent.bottom
            margins: defMargin
            verticalCenter: parent.verticalCenter
        }
        color: failure? palette.brightText: palette.text
    }

    TextField{
        id: _value
        anchors{
            right: 	parent.right
            left:	_name.right
            //bottom: parent.bottom
            verticalCenter: parent.verticalCenter
            leftMargin: defMargin
        }
        background: Rectangle{
            id: _bg
            XemLine{
                id: _underline
                anchors{
                    bottom: parent.bottom
                }
                width: _value.width
            }
        }

        color: _name.color
        cursorVisible: activeFocus
        selectByMouse: !passwordInput
        focus: true
        overwriteMode: true
        maximumLength: 20
        leftPadding: 10
//        rightInset: 10
        font{
            pixelSize: 14
        }
        //
        echoMode: passwordInput? TextInput.Password: TextInput.Normal
        passwordCharacter: "*"
        passwordMaskDelay: 3000

    }

    /*
    Rectangle{
        height: 1
        color: _name.color
        anchors{
            right: 	parent.right
            left:	_name.right
            top: _name.bottom
            topMargin: 5
            margins: defMargin
        }
    }
    */

}
