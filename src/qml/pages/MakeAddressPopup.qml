import QtQuick 2.12
import QtQuick.Controls 2.12

import "../js/functions.js" as Funcs
import "../controls"

BasePopup {
    id: _base
    ok: false
    acceptText: qsTr("Create")

    property alias coinName: _coin.value
    property alias label: _label.value
    readonly property int defFontSize: 14

    signal make(string label, bool segwit)

    onAccept: make(_label.value, _segwit.checked)
    focus: true
    width: 700
    height: 500

    onVisibleChanged: {
        _label.value = ""
        _message.value = ""
    }


        Column{
            anchors{
                fill: parent
                //margins: 20
            }
            spacing: 15

           DetailLabel{
               id: _coin
               name: qsTr("Currency:")
               nameTextSize: defFontSize
               valueTextSize: defFontSize
           }
           DetailInput{
               id: _label
               name: qsTr("Address label (optional):")
               nameFontSize: defFontSize
               defMargin: 10
               width: parent.width

               height: 30
               //placeholder: qsTr("any string to distinguish this address")
               bgColor: palette.midlight
           }
           SwitchBox{
               id: _segwit
               checked: true
               text: qsTr("Segwit address:")
               anchors{
                   left: _label.left
                   leftMargin: _label.inputX + defMargin
                   right: _label.right
               }
           }

           LongInput{
               id: _message
               name: qsTr("Message")
               height: 200
               width: parent.width
               anchors{
                   left: _label.left
                   right: _label.right
               }
               bgColor: palette.midlight
               nameFontSize: defFontSize
           }
        }
}
