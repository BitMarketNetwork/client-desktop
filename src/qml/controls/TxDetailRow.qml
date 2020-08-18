import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"

Base{
    id: _base

    property alias name: _tx_key.text
    property alias value: _tx_value.text
    property alias unit: _tx_unit.text
    property alias font: _tx_key.font

    height: _tx_key.font.pixelSize
    width: childrenRect.width

    SmallLabel{
        id: _tx_key
        anchors{
            verticalCenter: parent.verticalCenter
            left: parent.left
        }

        font.pixelSize: 14
        color: palette.text
    }
    SmallLabel{
        id: _tx_value
        anchors{
            verticalCenter: parent.verticalCenter
            left: _tx_key.right
            leftMargin: 10
        }
        font.pixelSize: 12
        color: palette.text
    }
    SmallLabel{
        id: _tx_unit
        anchors{
            verticalCenter: parent.verticalCenter
            left: _tx_value.right
            leftMargin: 10
        }
        font.pixelSize: 12
        color: palette.text
    }
}

