import QtQuick 2.12

Base {
    property alias time: _tx_time.value
    property alias confirm: _tx_confirm.value
    // property alias hash: _tx_id.value

    Column{
        anchors{
            fill: parent
            leftMargin: 5
        }
        spacing: 1

        TxDetailRow {
            anchors{
                left: parent.left
            }

            id: _tx_time
            height: 16
            name: qsTr("Time:", "Cell in transaction list")
            font.pixelSize: 14
        }

        TxDetailRow {
            anchors{
                left: parent.left
            }
            font.pixelSize: 14
            id: _tx_confirm
            name: qsTr("Confirmations:", "Cell in transaction list")
        }
    }
}
