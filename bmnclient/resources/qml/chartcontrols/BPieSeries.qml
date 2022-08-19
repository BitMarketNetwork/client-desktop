import QtQuick
import QtCharts

PieSeries {
    id: _base
    size: 0.7
    holeSize: 0.3

    onSliceAdded: (slice) => {
        slice.labelPosition = PieSlice.LabelInsideHorizontal
        slice.labelVisible = true
        slice.explodeDistanceFactor = 0.01

        slice.onHovered.connect(function(hovered) {
            slice.exploded = hovered
        })
    }
}
