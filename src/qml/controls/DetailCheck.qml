import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"

Base {

    property alias name:    _name.text
    property alias checked: _check.checked
    property alias color: _name.color
    property alias fontSize: _name.font.pixelSize

    height: 40
    width: parent.width

    InfoLabel{
        id: _name
        anchors{
            left: parent.left
            leftMargin: 10
            verticalCenter: parent.verticalCenter
        }
        font{
            pixelSize: 16
        }

        effect: true
    }
    Switch{
        id: _check
        anchors{
            verticalCenter: parent.verticalCenter
            left: _name.right
            leftMargin: defMargin
        }
    }
}
