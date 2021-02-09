import QtQuick 2.15

BControl {
    id: _base
    default property alias children: _stack.children
    property alias stackItem: _stack
    property alias currentIndex: _tabBar.currentIndex

    contentItem: BColumnLayout {
        spacing: _base.spacing

        BTabBar {
            id: _tabBar
            BLayout.fillWidth: true
            position: BTabBar.Header

            Repeater {
                model: _stack.children.length
                delegate: BTabButton {
                    text: _stack.children[index].title
                }
            }
        }

        BStackLayout {
            id: _stack
            BLayout.fillWidth: true
            BLayout.fillHeight: true
            currentIndex: _tabBar.currentIndex
        }
    }
}
