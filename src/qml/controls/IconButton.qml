import QtQuick 2.12
import QtQuick.Controls 2.12

Image {
    id: _base

    property alias down: _area.pressed

    height: 40
    width: 40
    sourceSize{
        width: 40
        height: 40
    }

    property alias icon: _base.source

    signal click()
    MouseArea{
        id: _area
        anchors.fill: parent
        onClicked: {
            _base.click()
        }
    }
}
