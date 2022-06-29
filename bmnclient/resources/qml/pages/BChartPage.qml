import QtQuick
import QtCharts
import "../application"
import "../basiccontrols"
import "../coincontrols"
import "../chartcontrols"

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

        BChartView {
            id: _chart
            visible: _pieSeries.sum > 0

            VPieModelMapper {
                series: _pieSeries
                model: BBackend.walletChart
                labelsColumn: 0
                valuesColumn: 1
                rowCount: model.rowCount()
            }

            BPieSeries {
                id: _pieSeries
            }

            BLogoImage {
                anchors.centerIn: parent
            }
        }
    }
}
