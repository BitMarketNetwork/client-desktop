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
    property alias address: _address.value
    property alias label: _label.value
    property  alias errorState: _error.visible
    readonly property int staticLabelWidth: 200

    signal validate()

    onAccept: validate()
    width: 800
    onVisibleChanged: {
        _label.value = ""
        _address.value = ""
    }


    function raiseError(message = null){
        errorState = message
        _error.text = message || "";

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
               labelWidth: staticLabelWidth
               width: parent.width - 40
           }
           DetailInput{
               id: _address
               name: qsTr("Address:")
               nameFontSize: 18
               width: parent.width - 40
               height: 50
               bgColor: palette.midlight
               maxLength: 48
               labelWidth: staticLabelWidth
               onValueChanged: {
                   raiseError()
               }
           }
           DetailInput{
               id: _label
               name: qsTr("Label (optional):")
               nameFontSize: 18
               defMargin: 10
               width: parent.width - 40
               height: 50
               bgColor: palette.midlight
               labelWidth: staticLabelWidth
               maxLength: 30
           }
           XemLine{
               red: errorState
               width: parent.width
               anchors{
               }
           }

           Label{
               id: _error
               horizontalAlignment: Text.AlignHCenter
               width: parent.width
               color: palette.brightText
               visible: false
           }
           Label{
               text: qsTr("Impossible to make transactions with this address. You can check the balance and view old transactions only")
               horizontalAlignment: Text.AlignHCenter
               width: parent.width
               color: palette.mid
           }
        }
}
