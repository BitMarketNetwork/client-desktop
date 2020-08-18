import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"

Rectangle {
    id: _base

    property bool online: true
    property alias message: _status_message.text

    color: palette.button
    height: 35


    Row{
        anchors{
            right: parent.right
            rightMargin: 20
            verticalCenter: parent.verticalCenter
            verticalCenterOffset: 5
        }
        spacing: 10

        Text{
            text: qsTr("Network status:","Status bar")
            color: palette.mid
            font{
                pixelSize: 14
            }
        }
        Text{
            text: _base.online? qsTr("Connected","Status bar"):qsTr("Disconnected","Status bar")
            color: palette.base
            font{
                pixelSize: 14
            }
        }

        Rectangle{
            anchors{
                bottom: parent.bottom
                bottomMargin: 5
            }
            id: _circle
            width: 21
            height: width
            radius: width * 0.5
            color: _base.online? palette.base: palette.brightText
        }
    }

    Text{
        id: _status_message
        color: palette.buttonText
        anchors{
            left: parent.left
            leftMargin: 20
            verticalCenter: parent.verticalCenter
        }
        font{
            pixelSize: 14
        }
    }
}
