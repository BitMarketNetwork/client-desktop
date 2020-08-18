import QtQuick 2.12
import "../controls"


Item	 {
    property string title: ""
    default property alias content: _content.children
    anchors.fill: parent

    Base {
        id: _content
        width: parent.width
        anchors{
            fill: parent
            topMargin: 10
        }
//        color: palette.base


    }
}
