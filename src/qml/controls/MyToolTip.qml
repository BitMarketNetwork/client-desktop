import QtQuick 2.0
import QtQuick.Controls 2.12
import "../controls"


ToolTip {

    background: Rectangle{
        radius: 10
        color: palette.light
    }
    contentItem: Text {
        id: _text
        text: _tip.text
        font{
        pixelSize: 16
        }
        color: palette.dark
    }
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
            duration: 2000
            easing.type:  Easing.OutCubic
        }
    }

}
