import QtQuick.Controls

ScrollView {
    padding: 0
    spacing: 0
    clip: true

    BScrollBar.vertical.policy: BScrollBar.vertical.size < 1 ? BScrollBar.AlwaysOn : BScrollBar.AlwaysOff
    BScrollBar.horizontal.policy: BScrollBar.horizontal.size < 1 ? BScrollBar.AlwaysOn : BScrollBar.AlwaysOff
}
