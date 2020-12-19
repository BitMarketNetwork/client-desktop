import QtQuick.Controls 2.15

ToolTip {
    x: (parent.width - implicitWidth) / 2
    y: parent.height
    width: implicitWidth
    height: implicitHeight

    visible: parent.hovered
    delay: _applicationStyle.tooTipDelay
    timeout: -1
}
