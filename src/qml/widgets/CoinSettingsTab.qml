import QtQuick 2.12
import QtQuick.Controls 2.12

import "../controls"

Tab {
    id: _base
    property alias model: _coin_list.model

        Component.onCompleted: {
            // console.log(`${parent.height} ${parent.height - 300}`)
        }
        onHeightChanged: {
            // console.log(`${parent.height} ${parent.height - 300}`)
        }

    TitleText{
        id: _title
        anchors{
            //horizontalCenter: parent.horizontalCenter
            left: parent.left
            top: parent.top
            leftMargin: 40
            topMargin: 10
        }
        text: qsTr("Uncheck unnecessary coins","Settings item")
        sub: true
    }

    Flickable{
        id: _scrollable
        anchors{
            top: _title.bottom
            topMargin: 10
            left: parent.left
            right: parent.right
//            bottom: parent.bottom
        }
        contentHeight: 400
        height: parent.height
        clip: true
        ScrollBar.vertical: ScrollBar{
            width: 30
            policy: ScrollBar.AlwaysOn
        }



        ListView{
            id: _coin_list
//            height: 400
//            clip: true
            anchors{
                fill: parent
            }
            delegate:
                Base {
                id: _coin
                height: 40
                width: _scrollable.width - 40

                SettingsCheckBox{
                    name: modelData.fullName
                    anchors{
                        fill: parent
//                        margins: 5
                    }
                    checked: modelData.visible
                    active: modelData.enabled
                    onCheckedChanged: {
                        modelData.visible = checked;
                    }
                }
            }
        }
    }
}
