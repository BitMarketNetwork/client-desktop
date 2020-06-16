import QtQuick 2.12
import QtGraphicalEffects 1.12
import "../controls"
import "../widgets"

Base {
    id: _base

    property alias name: _coin_name.text
    property alias icon: _coin_icon.source
    property string color : "yellow"
    property alias fontSize: _coin_name.font.pixelSize
    readonly property int icon_size: 45

    width: 80
    antialiasing: true

        Image {
            id: _coin_icon
            sourceSize.height: icon_size
            sourceSize.width: icon_size
            height: icon_size
            width: icon_size
            anchors.leftMargin: 16
            fillMode: Image.PreserveAspectFit
            smooth: true
            anchors{
                    verticalCenter: parent.verticalCenter
                    left: parent.left
                }
        }
        LabelText{
            id: _coin_name
            enabled: _base.enabled
            color: _base.enabled? _base.color : palette.mid
            anchors{
                    verticalCenter: parent.verticalCenter
                    left: parent.left
                    leftMargin: icon_size + 20
                }
        }
}
