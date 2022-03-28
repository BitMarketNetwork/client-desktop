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

        /*VPieModelMapper {
            series: pieSeries
            model: BBackend.coinList
            labelsColumn: 1
            valuesColumn: 4
            firstRow: 1
            rowCount: BBackend.coinList.rowCount()
        }*/

        PieSeries {
            id: pieSeries
            size: 0.7
            holeSize: 0.3

            BPieSlice { label: "btc"; value: 10334 }
            BPieSlice { label: "btc-testnet"; value: 3066 }
            BPieSlice { label: "ltc"; value: 6111 }

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
