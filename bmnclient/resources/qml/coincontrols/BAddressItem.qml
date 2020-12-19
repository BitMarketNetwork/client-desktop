import QtQuick 2.15
import QtQuick.Controls.Material 2.15
import "../application"
import "../basiccontrols"

BItemDelegate {
    id: _base
    property BAddressObject address: null
    property BMenu contextMenu: null

    text: {
        if (address.label && address.label.length > 0) {
            return address.label + " : " + address.name
        } else {
            return address.name
        }
    }

    // TODO address.updating: show animation

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
            color: address.watchOnly ? Material.hintTextColor : Material.foreground
        }
        BAmountLabel {
            font.pointSize: _base.font.pointSize * _applicationStyle.fontPointSizeFactor.small
            color: address.watchOnly ? Material.hintTextColor : Material.foreground
            amount: address.amount
        }

        Loader {
            active: _base.contextMenu !== null
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
        BBackend.uiManager.copyToClipboard(address.name)
    }

    // TODO right click
}
