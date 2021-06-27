import QtQml 2.15
import "../application"
import "../basiccontrols"
import "../coincontrols"

// TODO python control
BDialog {
    id: _base
    property var sourceList // TxFactorySourceListModel

    title: qsTr("Transaction inputs")
    contentItem: BDialogLayout {
        BDialogInputSwitch {
            id: _selectAll
            text: qsTr("Auto selection")
            onCheckedChanged: {
                _base.sourceList.useAllInputs = checked
            }
            Binding on checked {
                value: _base.sourceList.useAllInputs
            }
        }
        BDialogSeparator {}
        BAddressListView {
            BLayout.fillWidth: true
            BLayout.fillHeight: true
            BLayout.minimumHeight: 0
            BLayout.maximumHeight: implicitHeight

            visibleItemCount: Math.min(10, _base.sourceList.rowCount())
            model: _base.sourceList
            delegate: BAddressItem {
                address: model
                checkable: true
                enabled: !_selectAll.checked
                onCheckedChanged: {
                    model.state.useAsTransactionInput = checked
                }
                Binding on checked {
                    value: model.state.useAsTransactionInput
                }
            }
            templateDelegate: BAddressItem {
                address: BCommon.addressItemTemplate
                checkable: true
            }
        }
    }
    footer: BDialogButtonBox {
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
            text: BCommon.button.closeRole
        }
    }
}
