import QtQuick 2.12
import QtQuick.Controls 2.12
import "../js/functions.js" as Funcs
import "../controls"

BasePopup {

    id: _base
    acceptText: qsTr("Exchange")
    ok: false
    title: qsTr("Exchange summary")

    property alias sendAmount: _to_send.value
    property alias sendUnit: _to_send.unit
    property alias sendIcon: _send_icon.source
    property alias receiveAmount: _to_get.value
    property alias receiveUnit: _to_get.unit
    property alias receiveIcon: _receive_icon.source
    readonly property int icon_size: 45

    Grid{
        anchors{
            fill: parent
            margins: 20
        }
        spacing: 10
        columns: 2
        rows: 2
        Image {
            id: _send_icon
            anchors{
            }
            sourceSize.height: icon_size
            sourceSize.width: icon_size
            height: icon_size
            width: icon_size
            fillMode: Image.PreserveAspectFit
            smooth: true
            antialiasing: true
            cache: false
        }
        DetailLabel{
            id: _to_send
            name: qsTr("Amount of money to send:")
            value: "ddd"
            width: parent.width - _send_icon.width
        }
        Image {
            id: _receive_icon
            anchors{
            }
            sourceSize.height: icon_size
            sourceSize.width: icon_size
            height: icon_size
            width: icon_size
            fillMode: Image.PreserveAspectFit
            smooth: true
            cache: false
            antialiasing: true
        }
        DetailLabel{
            id: _to_get
            name: qsTr("Amount of money to get:")
            width: parent.width - _receive_icon.width
        }
    }
}
