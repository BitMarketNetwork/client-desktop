import QtQuick
import QtQuick.Layouts

import "../basiccontrols"

BControl {
    id: _base
    property var coin // CoinModel
    property BMenu contextMenu

    padding: _applicationStyle.padding
    contentItem: BRowLayout {
        BIconLabel {
            Layout.fillWidth: true
            icon.width: _applicationStyle.icon.largeWidth
            icon.height: _applicationStyle.icon.largeHeight
            icon.source: _applicationManager.imagePath(_base.coin.iconPath)
            font.bold: true
            font.pointSize: _base.font.pointSize * _applicationStyle.fontPointSizeFactor.huge
            text: _base.coin.fullName
        }
        BAmountLabel {
            amount: _base.coin.balance

            MouseArea {
                anchors.fill: parent
                onDoubleClicked: {
                    BBackend.clipboard.text = "%1 %2 / %3 %4"
                                                .arg(_base.coin.balance.valueHuman)
                                                .arg(_base.coin.balance.unit)
                                                .arg(_base.coin.balance.fiatValueHuman)
                                                .arg(_base.coin.balance.fiatUnit)
                }
            }
        }
        BContextMenuToolButton {
            font.pointSize: _base.font.pointSize * _applicationStyle.fontPointSizeFactor.huge
            menu: _base.contextMenu
        }
    }
}
