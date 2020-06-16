import QtQuick 2.12
//import QtQuick.Shapes 1.13
import QtGraphicalEffects 1.12


Item {
    id: _base


    width: 500;  height: 100

    Item {
        id: _square

        anchors.centerIn: parent
        readonly property double minimum: Math.min(_base.width, _base.height)

        width: minimum;
        height: minimum

        Repeater {
            id: _repeater

            model: 8

            delegate: Rectangle{
                color: palette.dark
                /*
                gradient: RadialGradient{
                    centerX: width* 0.5; centerY:height* 0.5
                    //centerRadius: width* 0.5
                    //focalX: centerX; focalY: centerY
                    GradientStop { position: 0; color: "blue" }
                    GradientStop { position: .3; color: "white" }
                    GradientStop { position: 1; color: "cyan" }
                }
                */

                property double b: 0.1
                property double a: 0.2

                width: ((b - a) / _repeater.count * index + a) * _square.height;
                height: width
                radius: 0.5 * height
                opacity: index*.08 + 0.1

                x: (0.5 - index*.0) * _square.width  + 0.5 * (_square.width  - width )  * Math.cos(2 * Math.PI / _repeater.count * index) - 0.5 * width
                y: (0.5 - index*.0) * _square.height - 0.5 * (_square.height - height)  * Math.sin(2 * Math.PI / _repeater.count * index) - 0.5 * height
            }
        }

        RadialBlur{

            anchors.fill: _square
            source: _square
            samples: 24
            angle: 10
        }
    }

    Timer {
        interval: 10
        running: true
        repeat:  true

        onTriggered: {
            _square.rotation += 2;
        }
    }
}
