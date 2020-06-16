import QtQuick 2.12
import QtQuick.Controls 2.12

import "../js/functions.js" as Funcs
import "../js/constants.js" as Constants

Base {
    id: _base

    property alias text: _label.text
    property alias address: _address_input.text
    property alias readOnly: _address_input.readOnly
    property bool  valid: true

    height: 50
    antialiasing: true

    signal changed()

    Column{
        anchors{
            fill: parent
            margins: 10
        }
        spacing: 5
        LabelText{
            id: _label
        }
        TextInput{
            anchors{
               left: parent.left
            }
            id: _address_input
            color: _base.valid? palette.windowText: Constants.invalidTextColor
            font.pixelSize: 14
            focus: true
            cursorVisible: true
            width: 500
            maximumLength: 80
            inputMethodHints: Qt.ImhPreferUppercase
            padding: 5
            onTextEdited:{
                changed()
            }

        }
        Rectangle{
            id: _border
            height: 2
            width: 450
            color: palette.dark
        }
    }
}
