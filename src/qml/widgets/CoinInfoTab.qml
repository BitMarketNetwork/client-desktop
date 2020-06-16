import QtQuick 2.12
import "../controls"

Item {
    id: _base

    property alias  name: _name.value
    property alias  versionHuman: _version_str.value
    property alias  versionNum: _version_num.value
    property alias  coinHeight: _height.value
    property bool 	online: true

    property color valueColor: online ? palette.text : palette.mid

    readonly property color color: palette.dark

    Column{
        anchors{
            fill: parent
//            margins: 10
        }

        AboutLabel{
            id: _name
            valueColor: _base.valueColor
            name: qsTr("Coin name:")
        }
        AboutLabel{
            id: _online
            valueColor: _base.valueColor
            name: qsTr("Coin status:")
            value: online? qsTr("Online") : qsTr("Offline")
        }
        AboutLabel{
            id: _version_str
            valueColor: _base.valueColor
            name: qsTr("Daemon human version:")
        }
        AboutLabel{
            id: _version_num
            valueColor: _base.valueColor
            name: qsTr("Daemon numeric version:")
        }
        AboutLabel{
            id: _height
            valueColor: _base.valueColor
            name: qsTr("Coin height:")
        }
    }
}
