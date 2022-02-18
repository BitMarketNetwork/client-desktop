import QtQuick
import QtQuick.Controls.Material
import "../basiccontrols"

BItemDelegate {
    id: _base
    property var address // AddressModel
    property BMenu contextMenu

    text: (address.state.label ? address.state.label + " : " : "") + address.name

    // TODO address.state.isUpdating: show animation

    contentItem: BRowLayout {
        Loader {
            active: _base.checkable
            sourceComponent: BCheckBox {
                id: _checkBox
                Binding {
                    target: _base
                    property: "checked"
                    value: _checkBox.checked
                }
                Binding {
                    target: _checkBox
                    property: "checked"
                    value: _base.checked
                }
            }
        }
        BLabel {
            BLayout.fillWidth: true
            elide: BLabel.ElideMiddle
            text: _base.text
        }
        BAmountLabel {
            font.pointSize: _base.font.pointSize * _applicationStyle.fontPointSizeFactor.small
            font.strikeout: _base.address.state.isReadOnly // TODO tmp
            amount: _base.address.balance
        }
        Loader {
            active: _base.contextMenu
            sourceComponent: BContextMenuToolButton {
                menu: null
                onClicked: {
                    _base.contextMenu.address = _base.address
                    toggleMenu(_base.contextMenu)
                }
            }
        }
    }

    onDoubleClicked: {
        BBackend.clipboard.text = address.name
    }

    // TODO right click
}
