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
                maximumLineCount: 50
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
            BLayout.fillWidth: true
            BLayout.fillHeight: true
            active: model.column == 2
            sourceComponent: BColumnLayout {

                BRowLayout {
                    BLayout.alignment: Qt.AlignRight
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
