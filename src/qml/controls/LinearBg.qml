import QtQuick 2.0
import QtQuick.Shapes 1.12

LinearGradient{

    property alias colorOne: _one.color
    property alias colorTwo: _two.color

    spread: ShapeGradient.RepeatSpread
    stops: [
        GradientStop {
            id: _one
            position: 0.1;
        },
        GradientStop {
            id: _two
            position: 0.5;
        },
        GradientStop {
            id: _three
            color: colorOne
            position: 1.0;
        }
    ]

    x1: 0
    x2: width * 0.3
    y1: 0
    y2: height * 0.5
}
