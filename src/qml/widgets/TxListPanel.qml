import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../widgets"
import "../api"
import "../js/functions.js" as Funcs



Base {
    id: _base
    property alias model: _list.model
    property bool isUpdating



        XemLine{
            anchors{
                rightMargin: 20
                leftMargin: 20
                top: parent.top
            }
            id: _tx_line
            blue: false
        }

    ListView{
        id: _list
        anchors.fill: parent
        clip: true

        footer: TxListFooter{
            visible: _base.isUpdating
        }

        delegate: TxDelegate{
            id: _me
            width: _tx_list.width
            tx: model
            onTxClick:{
                expanded = !expanded
            }
        }
    }
}
