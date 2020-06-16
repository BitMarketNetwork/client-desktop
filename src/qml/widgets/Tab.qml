import QtQuick 2.12
import "../controls"


Base	 {
    property string title: ""
    default property alias content: _content.children
    anchors.fill: parent

    Rectangle {
        id: _content
        width: parent.width
        anchors{
            fill: parent
            topMargin: defaultMargin
        }
        color: palette.base


    }
}
