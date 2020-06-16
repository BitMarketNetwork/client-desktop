import QtQuick 2.12
import QtQuick.Controls 2.12
import QtGraphicalEffects 1.12
import "../controls"
import "../api"
import "../widgets"
import "../pages"

Rectangle {
    id: _base
    radius: 10
    color: palette.base

    property alias title: _title.text
    property alias titleColor: _title.color

    default property alias content__: _content.children

    state: "attached"

    readonly property int defMargin: 20
    readonly property int 	defLeftMargin: 150

    /*
    InnerShadow {
            id: _shadow
            anchors.fill: _base
            cached: true
            horizontalOffset: -3
            verticalOffset: -3
            radius: 1.0
            samples: 8
            color: defTextColor
            source: _base
        }
    */

    // there's no need for child item but let it be for future
    Base{

        id: _content
        antialiasing: true

        anchors{
            fill: parent
        }


        LabelText{
            id: _title
            anchors{
                top: parent.top
                left: parent.left
                margins: defMargin
            }
        }
    }

    XemLine{
        anchors{
            bottom: parent.bottom
        }
        width: parent.width
        blue: false
    }
    XemLine{
        anchors{
            top: parent.top
        }
        width: parent.width
        blue: false
        visible: false
    }

    states: [
        State {
            name: "attached"

            AnchorChanges {
                target: _base
                anchors.left: parent.left
                anchors.right: parent.right
            }
        },
        State {
            name: "left"

            AnchorChanges {
                target: _base
                anchors.left: parent.left
                anchors.right: parent.horizontalCenter
            }
        },
        State {
            name: "right"

            AnchorChanges {
                target: _base
                anchors.left: parent.horizontalCenter
                anchors.right: parent.right
            }
        }
    ]
}
