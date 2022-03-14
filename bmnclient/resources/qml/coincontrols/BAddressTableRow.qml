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
            active: model.column == 0
            sourceComponent: BLabel {
                BLayout.preferredWidth: parent.width * 0.20
                BLayout.maximumWidth: parent.width * 0.20
                elide: BLabel.ElideMiddle
                maximumLineCount: 20
                text: _base.address.name
            }
        }
        Loader {
            active: model.column == 1
            sourceComponent: BLabel {
                BLayout.preferredWidth: parent.width * 0.10
                BLayout.maximumWidth: parent.width * 0.10
                elide: BLabel.ElideRight
                maximumLineCount: 20
                text: address.state.label
            }
        }
        /*Item { //spacer
            BLayout.preferredWidth: parent.width * 0.50
            BLayout.maximumWidth: parent.width * 0.50
            BLayout.fillHeight: true
        }*/
        Loader {
            active: model.column == 2
            sourceComponent: BAmountLabel {
                font.pointSize: _base.font.pointSize * _applicationStyle.fontPointSizeFactor.small
                font.strikeout: _base.address.state.isReadOnly // TODO tmp
                amount: _base.amount
            }
        }
        Loader {
            active: model.column == 3
            sourceComponent: Item {
                BLayout.preferredWidth: parent.width * 0.05
                BLayout.maximumWidth: parent.width * 0.05
                BLabel {
                    anchors.centerIn: parent
                    elide: BLabel.ElideRight
                    maximumLineCount: 4
                    text: _base.address.txList.rowCount()
                }
            }
        }
        Loader {
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
        BBackend.clipboard.text = address.name
    }

    // TODO right click
}
