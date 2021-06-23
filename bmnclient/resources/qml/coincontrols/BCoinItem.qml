import QtQuick 2.15
import "../basiccontrols"

BItemDelegate {
    id: _base
    property var coin // CoinModel

    text: coin.fullName
    icon.source: _applicationManager.imagePath(coin.iconPath)

    contentItem: BRowLayout {
        BIconLabel {
            BLayout.fillWidth: true
            display: _base.display
            icon: _base.icon
            text: _base.text
        }
        BAmountLabel {
            // if we hide this item, width of BItemDelegate will be changed...
            BLayout.leftMargin: _base.display === BItemDelegate.TextBesideIcon ? _base.fontMetrics.averageCharacterWidth * 3 : 0
            BLayout.minimumWidth: BLayout.preferredWidth
            BLayout.preferredWidth: _base.display === BItemDelegate.TextBesideIcon ? implicitWidth : 0
            BLayout.maximumWidth: BLayout.preferredWidth

            clip: true
            font.pointSize: Math.round(_base.font.pointSize * _applicationStyle.fontPointSizeFactor.small)
            amount: _base.coin.amount
        }
    }

    toolTipItem: BToolTip {
        parent: _base
        contentItem: BColumnLayout {
            BLabel {
                text: _base.text
                BLayout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
            }
            BSeparator {
                BLayout.fillWidth: true
            }
            BAmountLabel {
                BLayout.alignment: Qt.AlignVCenter | Qt.AlignRight
                amount: _base.coin.amount
            }
        }
    }
}
