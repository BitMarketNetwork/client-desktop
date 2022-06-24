import QtCharts
import QtQuick
import "../application"
import "../basiccontrols"
import "../coincontrols"

Item {
    id: _base

    ChartView {
        id: chart
        title: "Chart View draft"
        anchors.fill: parent
        legend.visible: false
        antialiasing: true
        backgroundColor: "transparent"
        animationOptions: ChartView.SeriesAnimations

        VPieModelMapper {
            series: pieSeries
            model: BBackend.chartModel
            labelsColumn: 0
            valuesColumn: 1
            rowCount: BBackend.chartModel.rowCount()
        }

        PieSeries {
            id: pieSeries
            size: 0.7
            holeSize: 0.3

            onSliceAdded: (slice) => {
                slice.labelPosition = PieSlice.LabelInsideNormal
                slice.labelVisible = true
            }
        }

        BLogoImage {
            anchors.centerIn: parent
        }
    }
}
