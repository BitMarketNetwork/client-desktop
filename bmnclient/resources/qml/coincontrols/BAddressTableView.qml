import QtQuick
import Qt.labs.qmlmodels
import "../basiccontrols"

BTableView {
    id: _base
    
    property var columnWidthsInPercent
    
    columnWidthProvider: function (column) { 
        if (_base.model) {
            return (_base.width * columnWidthsInPercent[column]) / 100
        } else {
            return 0
        }
    }
    onWidthChanged: {
        _base.forceLayout()
    }
}
