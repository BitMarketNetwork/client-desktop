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
    acceptText: qsTr("Send","New transaction summary")
    ok: false
    title: qsTr("Transaction summary","New transaction summary");
    width: 1000

    signal send()

    Column{
        anchors{
            fill: parent
            margins: 20
        }
        spacing: 10
        DetailLabel{
            id: _amount
            name: qsTr("Amount to be sent:","Send money result")
            valueTextSize: 14
        }
        DetailLabel{
            id: _target
            name: qsTr("Recipient address:","Send money result")
            valueTextSize: 14
        }
        DetailLabel{
            id: _fee
            name: qsTr("Fee:","Send money result")
            valueTextSize: 14
            unit: _amount.unit
        }
        DetailLabel{
            id: _change
            name: qsTr("Change:","Send money result")
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
