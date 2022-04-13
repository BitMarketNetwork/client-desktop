import QtQuick
import QtQuick.Controls.Material
import "../basiccontrols"

BItemDelegate {
    id: _base
    property var address // AddressModel
    property var amount // AmountModel
    property BMenu contextMenu
    property color color: enabled ? Material.foreground : Material.hintTextColor

    // TODO address.state.isUpdating: show animation

    contentItem: Loader {
        sourceComponent: {
            switch (model.column) {
                case 0:
                    _addressComponent
                break;
                case 1:
                    _labelComponent
                break;
                case 2:
                    _amountComponent
                break;
                case 3:
                    _txCountComponent
                break;
                case 4:
                    if (_base.contextMenu)
                        _menuComponent
                break;
                default: break;
            }
        }
    }
    Component {
        id: _addressComponent

        BLabel {
            verticalAlignment: Text.AlignVCenter
            elide: BLabel.ElideMiddle
            maximumLineCount: 50
            text: _base.address.name
        }
    }
    Component {
        id: _labelComponent

        BLabel {
            verticalAlignment: Text.AlignVCenter
            elide: BLabel.ElideRight
            maximumLineCount: 20
            text: address.state.label
        }
    }
    Component {
        id: _amountComponent

        BColumnLayout {
            BRowLayout {
                BLayout.alignment: Qt.AlignRight
                BLayout.topMargin: 10
                BLabel {
                    BLayout.alignment: Qt.AlignVCenter | Qt.AlignRight
                    font.bold: true
                    color: _base.color
                    font.pointSize: _base.font.pointSize * _applicationStyle.fontPointSizeFactor.small
                    font.strikeout: _base.address.state.isReadOnly // TODO tmp
                    text: _base.amount.valueHuman
                }
                BLabel {
                    BLayout.alignment: Qt.AlignVCenter | Qt.AlignLeft
                    color: _base.color
                    font.pointSize: _base.font.pointSize * _applicationStyle.fontPointSizeFactor.small
                    font.strikeout: _base.address.state.isReadOnly // TODO tmp
                    text: _base.amount.unit
                }
            }
            BRowLayout {
                BLayout.alignment: Qt.AlignRight
                BLayout.bottomMargin: 10
                BLabel {
                    BLayout.alignment: Qt.AlignVCenter | Qt.AlignRight
                    font.bold: true
                    color: _base.color
                    font.pointSize: _base.font.pointSize * _applicationStyle.fontPointSizeFactor.small
                    font.strikeout: _base.address.state.isReadOnly // TODO tmp
                    text: _base.amount.fiatValueHuman
                }
                BLabel {
                    BLayout.alignment: Qt.AlignVCenter | Qt.AlignLeft
                    color: _base.color
                    font.pointSize: _base.font.pointSize * _applicationStyle.fontPointSizeFactor.small
                    font.strikeout: _base.address.state.isReadOnly // TODO tmp
                    text: _base.amount.fiatUnit
                }
            }
        }
    }
    Component {
        id: _txCountComponent

        BLabel {
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: BLabel.ElideRight
            maximumLineCount: 4
            text: _base.address.txList.rowCount()
        }
    }
    Component {
        id: _menuComponent
        BContextMenuToolButton {
            menu: null
            onClicked: {
                _base.contextMenu.address = _base.address
                toggleMenu(_base.contextMenu)
            }
        }
    }
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.RightButton

        onClicked: (mouse) => {
            if (mouse.button === Qt.RightButton) {
                _base.contextMenu.address = _base.address
                _base.contextMenu.popup()
            }  
        }
        onPressAndHold: (mouse) => {
            if (mouse.source === Qt.MouseEventNotSynthesized) {
                _base.contextMenu.address = _base.address
                contextMenu.popup()
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
}
