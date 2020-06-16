
import QtQuick 2.12
import QtQuick.Controls 2.12

import "../controls"

SettingsControl{

    property alias checked: _switch.checked
    property alias active: _switch.enabled
    bold: _switch.checked


    Switch{
        id: _switch
        anchors{
            verticalCenter: parent.verticalCenter
            right: parent.right
            rightMargin: 40
        }
    }
}
