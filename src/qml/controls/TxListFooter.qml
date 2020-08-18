import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../widgets"

Item{
        id: _footer
        height: 40
        width: _list.width

    Rectangle{
        anchors{
            fill: parent
            margins: 10
        }

        color: palette.base

        Text{
            anchors{
                horizontalCenter: parent.horizontalCenter
                verticalCenter: parent.verticalCenter
            }

            text: qsTr("Updating ...","Transaction list")
            color: palette.mid
        }
    }
}
