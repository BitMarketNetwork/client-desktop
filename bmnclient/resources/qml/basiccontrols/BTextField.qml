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

    /*background: Rectangle {
        color: "transparent"
        radius: 2
        border.width: _base.activeFocus || _base.hovered ? 2 : 1
        border.color:
            _base.activeFocus ?
                _base.Material.accentColor :
                (_base.hovered ? Material.primaryTextColor : Material.hintTextColor)
    }

    leftPadding: fontMetrics.averageCharacterWidth
    rightPadding: fontMetrics.averageCharacterWidth
    topPadding: fontMetrics.height * 0.5
    bottomPadding: fontMetrics.height * 0.5*/

    onActiveFocusChanged: {
        if (activeFocus && readOnly) {
            selectAll()
        }
    }
}
