import QtQuick

TableView {
    id: _base
    clip: true

    BScrollBar.vertical: BScrollBar {
        // TODO view BScrollView
        policy: _base.contentHeight > _base.height ? BScrollBar.AlwaysOn : BScrollBar.AlwaysOff
        onVisibleChanged: {
            _base.updateImplicitWidth()
        }
    }
    BScrollBar.horizontal: BScrollBar {
        // TODO view BScrollView
        policy: _base.contentWidth > _base.width ? BScrollBar.AlwaysOn : BScrollBar.AlwaysOff
    }

    function updateImplicitWidth() {
        let width = 0
        for (let i = 0; i < count; ++i) {
            let item = itemAtIndex(i)
            if (item && item.implicitWidth > width) {
                width = item.implicitWidth
            }
        }
        implicitWidth = width + (BScrollBar.vertical.visible ? BScrollBar.vertical.width : 0)
    }
}
