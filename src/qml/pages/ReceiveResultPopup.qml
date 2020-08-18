import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../api"


BasePopup{
    id: _base
    ok: false
    rejectText: qsTr("Close","Receive money result page")
    acceptText: qsTr("Copy address")
    title: qsTr("Receive payment summary")

    property alias address: _address.value
    property alias label: _label.value
    property alias message: _message.value

    onAccept: {
       CoinApi.receive.toClipboard()
        _tip.show(qsTr("Address copied to clipboard"), 2000);
    }

    Column{
        anchors{
            fill: parent
            margins: 20
        }
        spacing: 10


        DetailLabel{
            id: _address
            name: qsTr("Recipient address:","Receive money result page")
            valueTextSize: 14

        }
        DetailLabel{
            id: _label
            name: qsTr("Label:")
            valueTextSize: 14
        }
        LongInput{
            id:_message
            name: qsTr("Message:")

            readOnly: true
            height: 150
            width: parent.width
//            labelWidth: 200
        }

    }
}
