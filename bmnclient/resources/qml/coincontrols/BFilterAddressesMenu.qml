import QtQuick

import "../basiccontrols"

BContextMenuToolButton {
    id: _base
    icon.source: _applicationManager.imagePath("filter-solid.svg")
    icon.width: _applicationStyle.icon.smallWidth
    icon.height: _applicationStyle.icon.smallHeight
    text: ""

    signal hideEmptyChanged(bool checked)

    enum FilterRole {
        HideEmpty = 1
    }

    menu: BMenu {
        id: _filterMenu
        closePolicy:  BMenu.CloseOnEscape | BMenu.CloseOnPressOutside

        BMenuItem {
            id: _hideEmptyItem
            checkable: true
            text: qsTr("Hide empty")

            onTriggered: {
                _base.hideEmptyChanged(_hideEmptyItem.checked)
            }
        }
    }
}
