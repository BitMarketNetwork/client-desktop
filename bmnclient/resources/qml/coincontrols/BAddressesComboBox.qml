import QtQuick
import QtQuick.Controls
import "../application"
import "../basiccontrols"

BComboBox {
    id: _base
    displayText: qsTr("Select addresses")

    popup: Popup {
        id: popup
        y: _base.height - 1
        width: _base.width
        implicitHeight: contentItem.implicitHeight
        padding: 0

        contentItem: BListView {
            implicitHeight: Math.min(contentHeight, _base.parent.height - _base.y)
            model: _base.delegateModel
        }
    }
    delegate: BControl {
        width: _base.popup.contentItem.viewWidth
        contentItem: BCheckDelegate {
            text: model.name
        }
    }
}
