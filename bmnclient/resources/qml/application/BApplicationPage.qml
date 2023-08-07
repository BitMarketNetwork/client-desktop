import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Material

import "../basiccontrols"

BControl {
    id: _base
    default property alias children: _stack.children

    property string title: ""
    property string placeholderText: ""

    property alias list: _list
    property alias stack: _stack

    contentItem: BRowLayout {
        BListView {
            id: _list
            Layout.fillHeight: true

            visible: count > 0
            highlightFollowsCurrentItem: true
            model: _stack.children.length - 1
            delegate: BItemDelegate {
                id: _item
                text: _stack.children[index + 1].title
                enabled: _stack.children[index + 1].enabled
                visible: _stack.children[index + 1].enabled
                icon.source: _stack.children[index + 1].iconPath
                contentItem: BIconLabel {
                    display: _item.display
                    icon: _item.icon
                    text: _item.text
                }
                onClicked: {
                    _stack.currentIndex = index + 1
                }
            }
        }
        Rectangle {
            Layout.fillHeight: true
            implicitWidth: _list.count > 0 ? _applicationStyle.dividerSize : 0
            visible: _list.count > 0
            color: Material.dividerColor
        }
        BStackLayout {
            id: _stack
            currentIndex: 0
            Layout.fillWidth: true
            Layout.fillHeight: true

            Loader {
                active: _stack.currentIndex === 0
                sourceComponent: BEmptyBox {
                    placeholderText: _base.placeholderText
                }
            }
        }
    }
}
