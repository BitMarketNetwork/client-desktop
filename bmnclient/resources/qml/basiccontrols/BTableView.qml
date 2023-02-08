import QtQuick

TableView {
    id: _base

    property real viewWidth: width - (BScrollBar.vertical.visible ? BScrollBar.vertical.width : 0)

    clip: true

    BScrollBar.vertical: BScrollBar {
        // TODO view BScrollView
        policy: _base.contentHeight > _base.height ? BScrollBar.AlwaysOn : BScrollBar.AlwaysOff
    }
    BScrollBar.horizontal: BScrollBar {
        // TODO view BScrollView
        policy: _base.contentWidth > _base.width ? BScrollBar.AlwaysOn : BScrollBar.AlwaysOff
    }
}
