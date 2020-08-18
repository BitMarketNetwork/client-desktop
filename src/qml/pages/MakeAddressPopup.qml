import QtQuick 2.12
import QtQuick.Controls 2.12

import "../js/functions.js" as Funcs
import "../controls"

BasePopup {
    id: _base
    ok: false
    acceptText: qsTr("Create","New address dialog")

    property alias coinName: _coin.value
    property alias label: _label.value
    readonly property int defFontSize: 14
    readonly property int staticLabelWidth: 200

    signal make(string label, bool segwit)

    onAccept: make(_label.value, _segwit.checked)
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
               name: qsTr("Currency:","New address dialog")
               nameTextSize: defFontSize
               valueTextSize: defFontSize
               labelWidth: staticLabelWidth
           }
           DetailInput{
               id: _label
               name: qsTr("Address label (optional):","New address dialog")
               nameFontSize: defFontSize
               defMargin: 10
               width: parent.width

               height: 30
               //placeholder: qsTr("any string to distinguish this address")
               bgColor: palette.midlight
               labelWidth: staticLabelWidth
           }
           SwitchBox{
               id: _segwit
               checked: true
               text: qsTr("Segwit address:","New address dialog")
               anchors{
                   left: _label.left
                   leftMargin: _label.inputX + defMargin
                   right: _label.right
               }
           }

           LongInput{
               id: _message
               name: qsTr("Message","New address dialog")
               height: 200
               width: parent.width
               anchors{
                   left: _label.left
                   right: _label.right
               }
               bgColor: palette.midlight
               nameFontSize: defFontSize
               labelWidth: staticLabelWidth
           }
        }
}
