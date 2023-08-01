import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material

TextField {
    id: _base
    property FontMetrics fontMetrics: FontMetrics { font: _base.font }

    //clip: true
    selectByMouse: true
    wrapMode: TextField.NoWrap
    // TODO context menu
    // https://stackoverflow.com/questions/49793284/os-edit-paste-menu-for-qt-quick-2-textfield/49875950
    // https://bugreports.qt.io/browse/QTBUG-35598

    onActiveFocusChanged: {
        if (activeFocus && readOnly) {
            selectAll()
        }
    }
}
