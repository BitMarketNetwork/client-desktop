import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../widgets"


Item {
    id: _base

    property alias newAddress : _chb.checked

    height: childrenRect.height
    antialiasing: true


    LabelText{
        id: _label
        anchors{
            top: parent.top
            left: parent.left
        }

        text: qsTr("Change:","New transaction window")
    }

    Rectangle{
        id: _frame
        anchors{
            left: parent.left
            right: parent.right
            top: _label.bottom
        }
        height: childrenRect.height
        radius: 10

        color: palette.light

        Column{
            anchors{
                fill: parent
                margins: 10
            }
            MyCheckBox{
                id: _chb
                text: qsTr("Send change to a new address","New transaction window")
            }
        }
    }
}
