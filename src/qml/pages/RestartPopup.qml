import QtQuick 2.12
import "../controls"

BasePopup {

    id: _base
    // acceptText: qsTr("Restart now")
    ok: true
    title: qsTr("Applying new settings","Restart conformation")

    InfoLabel{
        id: _text
        anchors{
            horizontalCenter: parent.horizontalCenter
            top: parent.top
            topMargin: 40
        }

        font{
            pixelSize: 20
        }

        text: qsTr("New style will be applied after next launch")
    }
}
