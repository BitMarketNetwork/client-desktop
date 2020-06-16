import QtQuick 2.12
import "../controls"


BasePopup {


    property alias amount:  _amount.value
    property alias target:  _target.value
    property alias change:  _change.value
    property alias changeAddress:  _change_address.value
    property alias fee:     _fee.value
    property alias unit:     _amount.unit

    id: _base
    acceptText: qsTr("Send")
    ok: false
    title: qsTr("Transaction summary","Send money result")
    width: 1000

    onFeeChanged: {
        console.log(`fee ${fee}`)
    }

    signal send()

    Column{
        anchors{
            fill: parent
            margins: 20
        }
        spacing: 10
        DetailLabel{
            id: _amount
            name: qsTr("Amount of money to be sent:","Send money result")
            valueTextSize: 14
        }
        DetailLabel{
            id: _target
            name: qsTr("Receiver address:","Send money result")
            valueTextSize: 14
        }
        DetailLabel{
            id: _fee
            name: qsTr("Comission is:","Send money result")
            valueTextSize: 14
            unit: _amount.unit
        }
        DetailLabel{
            id: _change
            name: qsTr("Change is:","Send money result")
            valueTextSize: 14
            unit: _amount.unit
        }
        DetailLabel{
            id: _change_address
            name: qsTr("Send change to:","Send money result")
            valueTextSize: 14
        }

    }

    onAccept: {
        send()
        close()
    }
}
