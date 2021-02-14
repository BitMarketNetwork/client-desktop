// JOK++
import QtQuick 2.15
import QtQml 2.15
import QtQuick.Controls.Material 2.15
import "../basiccontrols"

// SYNC: BAmountInput
BControl {
    id: _base
    property var amount // TransactionBroadcastFeeAmountModel
    property color color: _base.enabled ? _base.Material.foreground : _base.Material.hintTextColor
    property int validStatus: BDialogValidLabel.Status.Unset

    property TextMetrics valueTextMetrics: TextMetrics {
        text: _base.amount.valueHumanTemplate
        font: _valueField.font
    }

    contentItem: BRowLayout {
        spacing: _valueField.rightPadding

        BTextField {
            id: _valueField
            property bool isValid: true

            BLayout.preferredWidth: leftPadding + rightPadding + _base.valueTextMetrics.width

            validator: _base.amount.valueHumanValidator
            horizontalAlignment: BTextField.AlignRight
            placeholderText: qsTr("Amount")

            Binding on text {
                restoreMode: Binding.RestoreNone
                when: !_valueField.focus && _valueField.isValid
                value: _base.amount.amountPerKiBHuman
            }

            onTextEdited: {
                if (focus) {
                    _base.processValue()
                }
            }
        }
        BLabel {
            color: _base.color
            text: _base.amount.unit
        }
        BButton {
            text: qsTr("recommended")
            onClicked: {
                if (focus) {
                    _base.setDefaultValue()
                }
            }
        }
    }

    function processValue() {
        if (amount.setAmountPerKiBHuman(_valueField.text)) {
            _valueField.isValid = true
            validStatus = BDialogValidLabel.Status.Accept
        } else {
            _valueField.isValid = false
            validStatus = BDialogValidLabel.Status.Reject
        }
    }

    function setDefaultValue() {
        if (amount.setDefaultValue()) {
            // bindings will update the text
            _valueField.isValid = true
            _valueField.focus = false // paranoid
            validStatus = BDialogValidLabel.Status.Accept
        }
    }}
