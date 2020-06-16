import QtQuick 2.12
import QtQuick.Controls 2.12

import "../controls"
import "../js/functions.js" as Funcs
import "../js/constants.js" as Const

SettingsControl {
    id: _base
    property alias actionName: _action.text
    property alias actionFont: _action.font

    signal emitAction()

   TxButton{
        id: _action

        anchors{
            verticalCenter: parent.verticalCenter
            right: parent.right
            rightMargin: 40
        }

        width: controlWidth
        onClicked: emitAction()
        height: 30
        /*

        background: Rectangle{
            implicitHeight: 30
            color: palette.base
        }
        */

    }
}
