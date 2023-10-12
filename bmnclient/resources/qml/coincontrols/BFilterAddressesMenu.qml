import QtQuick

import "../basiccontrols"

BContextMenuToolButton {
    icon.source: _applicationManager.imagePath("filter-solid.svg")
    icon.width: _applicationStyle.icon.smallWidth
    icon.height: _applicationStyle.icon.smallHeight
    text: ""

    menu: BMenu {
        id: _filterMenu
        closePolicy:  BMenu.CloseOnEscape | BMenu.CloseOnPressOutside

        BMenuItem {
            checkable: true
            text: qsTr("Hide empty")

            onTriggered: {
                // TODO switch model
            }
        }
    }
}
