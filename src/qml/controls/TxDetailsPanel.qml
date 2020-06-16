import QtQuick 2.12
import QtQuick.Controls 2.12
import "../js/constants.js" as Const
import "../api"


 Base{
    id: _base
    property bool expanded: false
    property int topOffset: 0
    property alias txId: _tx_id.value
    property alias fee: _tx_fee.value
    property alias block: _tx_block.value
    property alias confirmText: _tx_confirm.value
   // property string bColor: ""

   MouseArea{
       anchors.fill: _rect
       onDoubleClicked:{
            CoinApi.ui.copyToClipboard(_tx_id.value)
       }
   }

    Rectangle{
        id: _rect
        /*
        gradient: LinearBg{
            colorTwo: palette.mid
            colorOne: palette.button
        }
        */
        color: palette.base

        /*
        border{
            id: _border
            width: 2
            color: bColor
        }
        */

        radius: 10
        antialiasing: true

        anchors{
            fill: parent
            leftMargin: 5
            rightMargin: 5
            bottomMargin: 5
            topMargin: 5
        }

        Column{
            id: _column
            anchors{
                top: _line.bottom
                left: parent.left
                leftMargin: 15
                topMargin: 5
            }
            spacing: 4

            TxDetailRow{
                id: _tx_id
                name: qsTr("ID:")
            }
            TxDetailRow{
                id: _tx_confirm
                name: qsTr("Confirmations:")
            }
            TxDetailRow{
                id: _tx_block
                name: qsTr("Block:")
            }
            TxDetailRow{
                id: _tx_fee
                name: qsTr("Fee:")
                unit: api.unit
            }
        /*
        TxDetailRow{
            id: _tx_status
            name: qsTr("Status:")
        }
        */

        /*
        RowLayout{
            TxInputListPanel{
            input: true
            width: _base.width * 0.5
            }
            TxInputListPanel{
            input: false
            width: _base.width * 0.5
            }
        }
        */
        }
        XemLine{
            id: _line
            blue: false
            width: parent.width * 0.5

            anchors{
                top: parent.top
//                right: parent.right
//                right: parent.horizontalCenter
//                left: parent.left
                horizontalCenter: parent.horizontalCenter
                leftMargin: 10
//                rightMargin: 0
                topMargin: _base.topOffset
            }
        }
    }
 }
