import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material

BScrollView {
    id: _view
    property alias color: _base.color
    property alias text: _base.text
    property alias placeholderText: _base.placeholderText
    property alias readOnly: _base.readOnly
    property alias selectByMouse: _base.selectByMouse
    property alias wrapMode: _base.wrapMode

    property int visibleLineCount: 10

    contentHeight:
        (_base.topPadding + _base.topPadding)
        + (_base.textMargin)
        + (_base.fontMetrics.height * visibleLineCount)

    TextArea {
        id: _base
        property FontMetrics fontMetrics: FontMetrics { font: _base.font }

        selectByMouse: true
        wrapMode: TextArea.Wrap

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
        }*/

        /*leftPadding: fontMetrics.averageCharacterWidth
        rightPadding:
            fontMetrics.averageCharacterWidth
            + (_view.BScrollBar.vertical.visible ? _view.BScrollBar.vertical.width : 0)
        topPadding: fontMetrics.height * 0.5
        bottomPadding:
            fontMetrics.height * 0.5
            + (_view.BScrollBar.horizontal.visible ? _view.BScrollBar.horizontal.height : 0)*/
    }

    onActiveFocusChanged: { // TODO read focus manuals
        if (activeFocus) {
            _base.forceActiveFocus(Qt.TabFocus)
        }
    }

    function clear() {
        _base.clear()
    }
}
