import QtQuick 2.12
import QtQuick.Controls 2.12

import "../js/functions.js" as Funcs
import "../controls"

BasePopup {
    id: _base
    ok: false
    acceptText: qsTr("Add")
    canBeAccepted: _address.value.length > 10

    property alias coinName: _coin.value

    signal add(string address, string label)

    onAccept: add(_address.value , _label.value)
    focus: true
    width: 800
    onVisibleChanged: {
        _label.value = ""
        _address.value = ""
    }


        Column{
            anchors{
                fill: parent
            }
            spacing: 10

           DetailLabel{
               id: _coin
               name: qsTr("Currency:")
               nameTextSize: 18
           }
           DetailInput{
               id: _address
               name: qsTr("Address:")
               nameFontSize: 18
               width: parent.width - 40
               height: 50
               bgColor: palette.midlight
               maxLength: 48
           }
           DetailInput{
               id: _label
               name: qsTr("Label (optional):")
               nameFontSize: 18
               defMargin: 10
               width: parent.width - 40
               height: 50
               bgColor: palette.midlight
               maxLength: 30
           }
           InfoLabel{
               text: qsTr("It is impossible to make transactions with this address. You can only view balance and explore old transactions")
               horizontalAlignment: Text.AlignHCenter
               width: parent.width
           }
        }
}