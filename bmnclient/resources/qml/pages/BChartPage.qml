import QtCharts
import QtQuick
import "../application"
import "../basiccontrols"
import "../coincontrols"

BControl {
    id: _base

    contentItem: BStackLayout {
        id: _stack
        currentIndex: _chart.visible ? 1 : 0

        Loader {
            active: _stack.currentIndex === 0
            sourceComponent: BEmptyBox {
                placeholderText: qsTr("Wallet is empty.")
            }
        }

        ChartView {
            id: _chart
            anchors.fill: parent
            legend.visible: false
            antialiasing: true
            backgroundColor: "transparent"
            animationOptions: ChartView.SeriesAnimations
            visible: _pieSeries.sum > 0

            VPieModelMapper {
                series: _pieSeries
                model: BBackend.walletChart
                labelsColumn: 0
                valuesColumn: 1
                rowCount: model.rowCount()
            }

            PieSeries {
                id: _pieSeries
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
}
