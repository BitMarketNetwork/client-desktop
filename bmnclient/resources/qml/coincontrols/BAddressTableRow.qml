import QtQuick
import QtQuick.Controls.Material
import "../basiccontrols"

BItemDelegate {
    id: _base
    property var address // AddressModel
    property var amount // AmountModel
    property BMenu contextMenu

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
        Loader {
            BLayout.fillWidth: true
            active: model.column == 0
            sourceComponent: BLabel {
                elide: BLabel.ElideMiddle
                maximumLineCount: 20
                text: _base.address.name
            }
        }
        Loader {
            BLayout.fillWidth: true
            active: model.column == 1
            sourceComponent: BLabel {
                elide: BLabel.ElideRight
                maximumLineCount: 20
                text: address.state.label
            }
        }
        Loader {
            BLayout.alignment: Qt.AlignVCenter | Qt.AlignRight
            active: model.column == 2
            sourceComponent: BAmountLabel {
                font.pointSize: _base.font.pointSize * _applicationStyle.fontPointSizeFactor.small
                font.strikeout: _base.address.state.isReadOnly // TODO tmp
                amount: _base.amount
            }
        }
        Loader {
            BLayout.fillWidth: true
            BLayout.fillHeight: true
            active: model.column == 3
            sourceComponent: BLabel {
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                elide: BLabel.ElideRight
                maximumLineCount: 4
                text: _base.address.txList.rowCount()
            }
        }
        Loader {
            BLayout.fillWidth: true
            active: model.column == 4 && _base.contextMenu
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
        if (model.column === 0) {
            BBackend.clipboard.text = address.name
        } else if (model.column === 1) {
            BBackend.clipboard.text = address.state.label
        } else if (model.column === 2) {
            BBackend.clipboard.text = "%1 %2 / %3 %4"
                .arg(amount.valueHuman)
                .arg(amount.unit)
                .arg(amount.fiatValueHuman)
                .arg(amount.fiatUnit)
        } else if (model.column === 3) {
            BBackend.clipboard.text = address.txList.rowCount()
        }
    }
    // TODO right click
}
