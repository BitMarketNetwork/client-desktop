import QtQuick 2.12
import QtQuick.Controls 2.12

import "../js/functions.js" as Funcs
import "../controls"

Base {
    id: _base
    property alias name: _name.text
    property alias nameFontSize: _name.font.pixelSize
    property alias value: _value.text
    property alias readOnly: _value.readOnly
    property alias color: _name.color
    property alias valueColor: _value.color
    property alias bgColor: _bg.color
    property alias placeHolder: _value.placeholderText
    property alias labelWidth: _name.width


    readonly property int maxLines: 8
    readonly property int margin: 20


        LabelText{
            id: _name
            font{
                pixelSize: 16
            }
            anchors{
                left: parent.left
                leftMargin: 0
                top: parent.top
                topMargin: 10
            }
        }

       TextArea{
       //TextEdit{
            id: _value
            anchors{
                left: _name.right
                top: _name.bottom
                bottom: parent.bottom
                right: parent.right
                rightMargin: 0
                margins: margin
            }
            color: _name.color
            wrapMode: TextEdit.Wrap
            leftPadding: 20
            // we need explicit size for wrapping to work
            clip: true
            background: Rectangle{
                id: _bg
                color: palette.base
                XemLine{
                    anchors{
                        bottom: parent.bottom
                    }
                    width: _value.width
                    blue: false
                }
            }
            font{
                pixelSize: 14
            }
            onTextChanged: {
                // console.log(`lines count ${lineCount}`);
                if( lineCount > maxLines ){
                    // good choice!
                    // undo()

                    remove(text.length - 1,text.length)
                }
            }
    }
}
