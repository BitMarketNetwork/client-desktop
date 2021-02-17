// JOK++
import QtQuick 2.15
import QtQml 2.15
import QtQuick.Controls.Material 2.15
import "../basiccontrols"

// SYNC: BFeeAmountInput
BControl {
    id: _base
    property var amount // AmountInputModel
    property color color: _base.enabled ? _base.Material.foreground : _base.Material.hintTextColor
    property int orientation: Qt.Vertical

    property TextMetrics valueTextMetrics: TextMetrics {
        text: _base.amount.valueHumanTemplate
        font: _valueField.font
    }

    contentItem: BGridLayout {
        columns: _base.orientation === Qt.Vertical ? 3 : 7
        columnSpacing: _valueField.rightPadding
        rowSpacing: _valueField.bottomPadding

        BTextField {
            id: _valueField

            BLayout.column: 0
            BLayout.row: 0
            BLayout.preferredWidth: leftPadding + rightPadding + _base.valueTextMetrics.width

            validator: _base.amount.valueHumanValidator
            horizontalAlignment: BTextField.AlignRight
            placeholderText: qsTr("Amount")

            Binding on text {
                restoreMode: Binding.RestoreNone
                when: !_valueField.focus && _base.amount.validStatus === BDialogValidLabel.Status.Accept
                value: _base.amount.valueHuman
            }

            onTextEdited: {
                if (focus) {
                    _base.amount.setValueHuman(text)
                    _fiatValueField.focus = false // paranoid
                }
            }
        }
        BLabel {
            BLayout.column: 1
            BLayout.row: 0

            color: _base.color
            text: _base.amount.unit
        }

        Loader {
            active: _base.orientation !== Qt.Vertical
            sourceComponent: BLabel {
                BLayout.column: 2
                BLayout.row: 0
                font.bold: true
                color: _base.color
                text: "/"
            }
        }

        BTextField {
            id: _fiatValueField

            BLayout.column: _base.orientation === Qt.Vertical ? 0 : 3
            BLayout.row: _base.orientation === Qt.Vertical ? 1 : 0
            BLayout.preferredWidth: leftPadding + rightPadding + _base.valueTextMetrics.width

            validator: _base.amount.fiatValueHumanValidator
            horizontalAlignment: BTextField.AlignRight
            placeholderText: qsTr("Fiat amount")

            Binding on text {
                restoreMode: Binding.RestoreNone
                when: !_fiatValueField.focus && _base.amount.validStatus === BDialogValidLabel.Status.Accept
                value: _base.amount.fiatValueHuman
            }

            onTextEdited: {
                if (focus) {
                    _base.amount.setFiatValueHuman(text)
                    _valueField.focus = false // paranoid
                }
            }
        }
        BLabel {
            BLayout.column: _base.orientation === Qt.Vertical ? 1 : 4
            BLayout.row: _base.orientation === Qt.Vertical ? 1 : 0

            color: _base.color
            text: _base.amount.fiatUnit
        }

        Loader {
            active: _base.orientation !== Qt.Vertical
            sourceComponent: BLabel {
                BLayout.column: 5
                BLayout.row: 0

                font.bold: true
                color: _base.color
                text: "/"
            }
        }

        BButton {
            BLayout.column: _base.orientation === Qt.Vertical ? 2 : 6
            BLayout.row: 0
            BLayout.rowSpan: _base.orientation === Qt.Vertical ? 2 : 1

            text: qsTr("max")
            onClicked: {
                if (focus) {
                    _base.amount.setDefaultValue()
                    _valueField.focus = false // paranoid
                    _fiatValueField.focus = false // paranoid
                }
            }
        }
    }
}
