import QtQuick
import QtQuick.Controls.Material
import "../application"
import "../basiccontrols"

BItemDelegate {
    id: _base
    property var tx
    property string coinName
    property real smallFontPointSize: _base.font.pointSize * _applicationStyle.fontPointSizeFactor.small

    contentItem: BRowLayout {
        BLabel {
            BLayout.fillWidth: true
            elide: BLabel.ElideRight
            text: _base.tx.name
        }
        BColumnLayout {
            BLayout.fillHeight: true
            BLayout.alignment: Qt.AlignRight
            BLayout.leftMargin: 5

            BLabel {
                BLayout.alignment: Qt.AlignVCenter | Qt.AlignRight
                font.pointSize: _base.smallFontPointSize
                font.bold: true
                text: BCommon.txStatusMap[_base.tx.state.status][0]
                color: Material.color(BCommon.txStatusMap[_base.tx.state.status][1])
            }
            BAmountLabel {
                BLayout.alignment: Qt.AlignVCenter | Qt.AlignRight
                font.pointSize: _base.smallFontPointSize
                amount: _base.tx.amount
            }
        }
    }

    onClicked: {
        // TODO rework get %1
        Qt.openUrlExternally(("https://www.blockchain.com/%1/tx/%2")
            .arg(BCommon.txCoinNameMap.get(_base.coinName))
            .arg(_base.tx.name))
    }
}