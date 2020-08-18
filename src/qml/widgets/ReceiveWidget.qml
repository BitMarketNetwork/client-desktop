import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../api"
import "../widgets"
import "../pages"


SendWidget {
    id: _base
    title: qsTr("Label:")
    height: 350
    bottomLine: false

    property alias label: _label.text
    property alias segwit: _segwit.checked
    property alias message: _message.text



        TextField{
            id: _label
            anchors{
                left: parent.left
                leftMargin: defLeftMargin
                right: parent.right
                margins: defMargin
                top: parent.top
            }
            background: Rectangle{
                XemLine{
                    anchors{
                        bottom: parent.bottom
                    }
                    width: parent.width
                }
            }
            color: palette.mid
            cursorVisible: true
            selectByMouse: true
            overwriteMode: true
            maximumLength: 80
            leftPadding: 10
            rightInset: 10
        }

        SwitchBox{
            id: _segwit
            anchors{
                right: _label.right
                left: _label.left
                top:  _label.bottom
                topMargin: defMargin
            }
            text: qsTr("Segwit address:","Receive payment window")
            checked: true
        }

        LabelText{
            id: _message_label
            anchors{
                left: parent.left
                leftMargin: defMargin
                top:  _segwit.bottom
                topMargin: defMargin
            }
            text: qsTr("Message:","Receive payment window")
        }
       TextArea{
            id: _message
            readonly property int maxLines: 15

            anchors{
                left: parent.left
                leftMargin: defLeftMargin
                right: parent.right
                margins: defMargin
                top: _segwit.bottom
                bottom: parent.bottom
            }
            color: palette.mid
            wrapMode: TextEdit.Wrap
            leftPadding: 20
            // we need explicit size for wrapping to work
            width: _base.width - 20 * 2
            clip: true
            background: Rectangle{
                id: _bg
                color: palette.base
                XemLine{
                    anchors{
                        bottom: parent.bottom
                    }
                    width: _message.width
                }
            }
            font{
                pixelSize: 14
            }
            placeholderText: qsTr("Some text here ...","Receive money page")
            onTextChanged: {
                console.log(`lines count ${lineCount}`);
                if( lineCount > maxLines ){
                    // good choice!
                    // undo()

                    remove(text.length - 1,text.length)
                }
            }
        }
}
