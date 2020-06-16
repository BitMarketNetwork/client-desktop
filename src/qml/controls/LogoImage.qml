import QtQuick 2.12
import QtGraphicalEffects 1.12
import "../js/functions.js" as Funcs


Base {
    width: 200
    height: 40

    Image {
        anchors.fill: parent
        id: _logo
        antialiasing: true
        source: Funcs.loadImage("main_logo.png")
    }
    DropShadow {
        enabled: false
        anchors.fill: _logo
        horizontalOffset: 5
        verticalOffset: 3
        radius: 8.0
        samples: 20
        color: "#80000000"
        source: _logo
    }
    /*
    RadialBlur {
        anchors.fill: _logo
        source: _logo
        samples: 5
        transparentBorder: true
        angle: 10
    }
    */

    Glow {
        anchors.fill: _logo
        radius: 2
        samples: 10
        color: "grey"
        source: _logo
    }
}
