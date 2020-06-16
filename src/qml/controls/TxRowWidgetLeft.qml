import QtQuick 2.12

Base {
    property alias time: _tx_time.value
    property alias from: _tx_from.value
    property alias to: _tx_to.value

    TxDetailRow {
        anchors{
            left: parent.left
            top: parent.top
            margins: 5
        }

        id: _tx_time
        height: 16
        name: qsTr("Time:")
        font.pixelSize: 14
    }

    TxDetailRow {
        anchors{
            left: parent.left
            verticalCenter: parent.verticalCenter
            margins: 5
        }
        id: _tx_from
        name: qsTr("From:")
        font.pixelSize: 14
    }
    TxDetailRow {
        anchors{
            left: parent.left
            bottom: parent.bottom
            margins: 5
        }
        id: _tx_to
        name: qsTr("To:")
        font.pixelSize: 14
    }
}
