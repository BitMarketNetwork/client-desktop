// JOK++
import QtQml 2.15
import "../application"
import "../basiccontrols"
import "../coincontrols"

BDialog {
    id: _base
    property var inputList // TransactionBroadcastInputListModel

    title: qsTr("Transaction inputs")
    contentItem: BDialogLayout {
        BDialogInputSwitch {
            id: _selectAll
            text: qsTr("Auto selection")
            onCheckedChanged: {
                _base.inputList.useAllInputs = checked
            }
            Binding on checked {
                value: _base.inputList.useAllInputs
            }
        }
        BDialogSeparator {}
        BAddressListView {
            BLayout.fillWidth: true
            BLayout.fillHeight: true
            BLayout.minimumHeight: 0
            BLayout.maximumHeight: implicitHeight

            visibleItemCount: Math.min(10, _base.inputList.rowCount())
            model: _base.inputList
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
                address: BStandardText.addressItemTemplate
                checkable: true
            }
        }
    }
    footer: BDialogButtonBox {
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
            text: BStandardText.button.closeRole
        }
    }
}
