import QtQuick
import Qt.labs.qmlmodels
import "../basiccontrols"

BTableView {
    id: _base

    property var columnWidth

    columnWidthProvider: function (column) {
        if (_base.model) {
            if (columnWidth[column] == -1) { //spacer col
                let spacer_width = _base.viewWidth
                for(let col = 0; col < columnWidth.length; col++) {
                    if(columnWidth[col] != -1) spacer_width -= columnWidth[col];
                }
                return spacer_width
            } else {
                return columnWidth[column]
            }

        } else {
            return 0
        }
    }
    onWidthChanged: {
        _base.forceLayout()
    }
    onVisibleChanged: {
        _base.forceLayout()
    }
    Component.onCompleted: {
        _base.forceLayout()
    }
}
