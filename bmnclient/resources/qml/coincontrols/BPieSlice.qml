import QtCharts
import QtQuick
import "../application"
import "../basiccontrols"

PieSlice {
    id: _base
    explodeDistanceFactor: 0.05

    onHovered: (hovered) => { _base.exploded = hovered }
}
