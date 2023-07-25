import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Material

import "../application"
import "../basiccontrols"

BItemDelegate {
    id: _base
    property var tx
    property real smallFontPointSize: _base.font.pointSize * _applicationStyle.fontPointSizeFactor.small

    contentItem: BRowLayout {
        BLabel {
            Layout.fillWidth: true
            elide: BLabel.ElideRight
            text: _base.tx.name
        }
        BColumnLayout {
            Layout.fillHeight: true
            Layout.alignment: Qt.AlignRight
            Layout.leftMargin: 5

            BLabel {
                Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
                font.pointSize: _base.smallFontPointSize
                font.bold: true
                text: BCommon.txStatusMap[_base.tx.state.status][0]
                color: Material.color(BCommon.txStatusMap[_base.tx.state.status][1])
            }
            BAmountLabel {
                Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
                font.pointSize: _base.smallFontPointSize
                amount: _base.tx.amount
            }
        }
    }

    onClicked: {
        BBackend.settings.blockchainExplorer.browse(_base.tx.object)
    }
}
