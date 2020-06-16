import QtQuick 2.12
import QtQuick.Controls 2.12

import "../controls"

Popup{
    id: _base
    property alias text: _text.text

    enter: Transition {
        NumberAnimation {
            property: "opacity";
            from: 0.0; to: 1.0
            duration: 500
            easing.type:  Easing.InCubic
        }
    }
    exit: Transition {
        NumberAnimation {
            property: "opacity";
            from: 1.0;
            to: 0.0
            duration: 1000
            easing.type:  Easing.OutCubic
        }
    }

    anchors.centerIn:parent

    width: 600
    height: 400
    modal: false
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    dim: true
    visible: false

    Text{
        id: _text
        anchors{
            margins: 40
            fill: parent
            bottomMargin: 60
        }
        horizontalAlignment: Text.AlignHCenter
        color: palette.text
        width: parent.width - 40
        wrapMode: Text.WrapAtWordBoundaryOrAnywhere
        font{
            pixelSize: 20
        }
    }
    XemLine{
        anchors{
            top: _text.bottom
            topMargin: 20
            horizontalCenter: parent.horizontalCenter
        }
        width: parent.width - 40
    }


    parent: Overlay.overlay

    background:
        Rectangle {
            color: palette.base
        }

    Timer{
        id: _timer
        interval: 5000
        onTriggered: {
            close()
        }
    }

    onVisibleChanged: {
        if(visible){
            _timer.start()
        }
    }

    MouseArea{
        anchors{
            fill: parent
        }
        onClicked: {
            close()
        }
    }

}
