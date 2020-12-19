import QtQuick.Controls 2.15

ScrollView {
    property real viewWidth:
        width
        - (leftPadding + rightPadding)
        - (BScrollBar.vertical.visible ? BScrollBar.vertical.width : 0)
    property real viewHeight:
        height
        - (topPadding + bottomPadding)
        - (BScrollBar.horizontal.visible ? BScrollBar.horizontal.height : 0)

    padding: 0
    spacing: 0
    clip: true

    // TODO where delegate for BScrollBar?
    BScrollBar.vertical.policy: BScrollBar.vertical.size < 1 ? BScrollBar.AlwaysOn : BScrollBar.AlwaysOff
    BScrollBar.horizontal.policy: BScrollBar.horizontal.size < 1 ? BScrollBar.AlwaysOn : BScrollBar.AlwaysOff
}
