// JOK++
import QtQuick 2.15
import QtQuick.Controls.Material 2.15
import "../application"
import "../basiccontrols"

BItemDelegate {
    id: _base
    property var address // AddressListModel item
    property BMenu contextMenu

    text: address ? (address.state.label ? address.state.label + " : " : "") + address.name : BStandardText.template.addressName

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
            color: _base.address && _base.address.state.watchOnly ? Material.hintTextColor : Material.foreground
        }
        BAmountLabel {
            font.pointSize: _base.font.pointSize * _applicationStyle.fontPointSizeFactor.small
            color: _base.address && _base.address.state.watchOnly ? Material.hintTextColor : Material.foreground
            amount: _base.address ? _base.address.amount : null
        }

        Loader {
            active: _base.address && _base.contextMenu
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
        if (_base.address) {
            BBackend.uiManager.copyToClipboard(_base.address.name)
        }
    }

    // TODO right click
}
