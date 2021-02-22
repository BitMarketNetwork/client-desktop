import QtQuick.Window 2.15
import "../application"

BToolButton {
    id: _base
    property BMenu menu

    font.bold: true
    text: BCommon.button.contextMenuRole

    onClicked: {
        if (menu) {
            toggleMenu(menu)
        }
    }

    function toggleMenu(menu) {
        if (menu.visible) {
            menu.dismiss()
        } else {
            function onMenuVisibleChanged() {
                down = menu.visible
                if (!menu.visible) {
                    menu.onVisibleChanged.disconnect(onMenuVisibleChanged)
                }
            }

            menu.onVisibleChanged.connect(onMenuVisibleChanged)
            menu.popup(_base, _applicationManager.calcPopupPosition(_base, menu.width, menu.height))
        }
    }
}
