import QtQuick 2.12
import QtQuick.Controls 2.12
import "../js/constants.js" as Const
import "../api"

Base{
    id: _base
    property bool expanded: false
    property alias fee: _tx_fee.value
    property alias block: _tx_block.value
    property alias hash: _tx_hash.value
    property variant inputsModel: []
    property variant outputsModel: []

    readonly property int topOffset: 40
    height: 140
    width: parent.width

    MouseArea{
        anchors.fill: parent
        onDoubleClicked: {
            CoinApi.ui.copyToClipboard(_tx_hash.value)
        }
    }

    Base{
        XemLine{
            anchors{
                top: parent.top
            }
            width: parent.width
            blue: false
        }
        anchors{
            top: parent.top
            left: parent.left
            right: parent.right
            topMargin: topOffset
            leftMargin: 20
        }
        id: _tx_id
        height: 15
    TxDetailRow {
        id: _tx_hash
            name: qsTr("ID:", "Cell in transaction list")
        anchors{
            fill: parent
        }
    }
    }

    Column{
        id: _column
        anchors{
//            top: parent.top
            top: _tx_id.bottom
            bottom: parent.bottom
            left: parent.left
            leftMargin: 20
            topMargin: 5
        }
        spacing: 4
        width: 100

        TxDetailRow{
            id: _tx_block
            name: qsTr("Block:", "Cell in transaction list")
        }
        TxDetailRow{
            id: _tx_fee
            name: qsTr("Fee:", "Cell in transaction list")
            unit: api.unit
        }
        TxDetailButton{
            id: _input_btn
            text: qsTr("Inputs:", "Cell in transaction list")
            width: _tx_block.width
            checked: false
            onCheckedChanged: {
                _output_btn.checked = !checked
            }
        }
        TxDetailButton{
            id: _output_btn
            text: qsTr("Outputs:", "Cell in transaction list")
            width: _tx_block.width
            checked: true
            onCheckedChanged: {
                _input_btn.checked = !checked
            }
        }
    }
    TxInputsView{
        id: _inputs
        width: parent.width * 0.67
        // height: parent.height - _tx_hash.height
        z: -1
        model: _input_btn.checked ? inputsModel: outputsModel
        anchors{
            right: parent.right
//            top: parent.top
            top: _tx_id.bottom
            bottom: parent.bottom

//            topMargin: topOffset
//            margins: 5
        }
    }
}
