import QtQuick
import QtQuick.Layouts

import "../basiccontrols"

BItemDelegate {
    id: _base
    property var coin // CoinModel

    text: coin.fullName
    icon.source: _applicationManager.imagePath(coin.iconPath)

    contentItem: BRowLayout {
        BIconLabel {
            Layout.fillWidth: true
            display: _base.display
            icon: _base.icon
            text: _base.text
        }
        BAmountLabel {
            // if we hide this item, width of BItemDelegate will be changed...
            Layout.leftMargin: _base.display === BItemDelegate.TextBesideIcon ? _base.fontMetrics.averageCharacterWidth * 3 : 0
            Layout.minimumWidth: Layout.preferredWidth
            Layout.preferredWidth: _base.display === BItemDelegate.TextBesideIcon ? implicitWidth : 0
            Layout.maximumWidth: Layout.preferredWidth

            clip: true
            font.pointSize: Math.round(_base.font.pointSize * _applicationStyle.fontPointSizeFactor.small)
            amount: _base.coin.balance
        }
    }

    toolTipItem: BToolTip {
        parent: _base
        contentItem: BColumnLayout {
            BLabel {
                text: _base.text
                Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
            }
            BSeparator {
                Layout.fillWidth: true
            }
            BAmountLabel {
                Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
                amount: _base.coin.balance
            }
        }
    }
}
