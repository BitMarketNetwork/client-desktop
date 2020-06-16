import QtQuick 2.12
import QtQuick.Controls 2.12
import "../api"
import "../controls"
import "../widgets"
import "../js/constants.js" as Constants
import "../js/functions.js" as Funcs


NewTxPage {
    id: _base
    readonly property int pageId: Constants.pageId.receive
    action: qsTr("Receive")
    actionIcon: Funcs.loadImage("receive-money.svg")


    onAccept: {
        CoinApi.receive.accept(
                    _body.segwit,
                    _body.label,
                    _body.message
                    );
        _result.open()
    }

    Column{
        id: _main_column
        anchors{
            fill: parent
            topMargin: 150
        }
        spacing: 20
        ReceiveWidget{
            anchors{

            }

            id: _body
        }
    }

    Item{
        visible: false
        ReceiveResultPopup{
            id: _result
            address: CoinApi.receive.address
            label: CoinApi.receive.label
            width: 500

            onReject: {
                popPage()
            }
        }
    }
}
