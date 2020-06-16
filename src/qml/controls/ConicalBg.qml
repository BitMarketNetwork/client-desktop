import QtQuick 2.0
import QtQuick.Shapes 1.12

ConicalGradient{

    property alias colorOne: _one.color
    property alias colorTwo: _two.color
    property alias stop: _one.position

    angle: 30
    spread: ShapeGradient.RepeatSpread
    centerX: width * 0.1
    centerY: height * 0.5
    stops: [
        GradientStop {
            id: _one
            position: 0.33;
        },
        GradientStop {
            id: _two
            position: 1.0;
        }
    ]
}
