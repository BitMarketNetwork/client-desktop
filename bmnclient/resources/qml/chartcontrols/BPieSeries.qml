import QtQuick
import QtCharts

import "../application"

PieSeries {
    id: _base
    size: _applicationStyle.chart.size
    holeSize: _applicationStyle.chart.holeSize

    onSliceAdded: (slice) => {
        slice.labelPosition = PieSlice.LabelInsideHorizontal
        slice.labelVisible = true
        slice.explodeDistanceFactor = _applicationStyle.chart.explodeDistanceFactor

        slice.onHovered.connect(function(hovered) {
            slice.exploded = hovered
        })
    }
}
