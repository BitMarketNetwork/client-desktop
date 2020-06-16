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
            name: qsTr("Target address:","Receive money result page")
            MyToolTip{
                id: _tip
                visible: false
            }
        }
        DetailLabel{
            id: _label
            name: qsTr("Label:")
        }

    }
}
