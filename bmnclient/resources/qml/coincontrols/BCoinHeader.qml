import "../basiccontrols"

BControl {
    id: _base
    property BCoinObject coin: null
    property BMenu contextMenu: null

    padding: _applicationStyle.padding
    contentItem: BRowLayout {
        BIconLabel {
            BLayout.fillWidth: true
            icon.width: _applicationStyle.icon.largeWidth
            icon.height: _applicationStyle.icon.largeHeight
            icon.source: _base.coin.iconSource
            font.bold: true
            font.pointSize: _base.font.pointSize * _applicationStyle.fontPointSizeFactor.huge
            text: _base.coin.name
        }
        BAmountLabel {
            amount: coin.amount
        }
        BContextMenuToolButton {
            font.pointSize: _base.font.pointSize * _applicationStyle.fontPointSizeFactor.huge
            menu: _base.contextMenu
        }
    }
}
