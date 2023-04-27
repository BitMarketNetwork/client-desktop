import QtQuick
import QtQml
import QtQuick.Layouts
import QtQuick.Controls.Material

import "../application"
import "../basiccontrols"

BControl {
    id: _base
    property var amount // AmountInputModel
    property color color: _base.enabled ? _base.Material.foreground : _base.Material.hintTextColor
    property int orientation: Qt.Vertical
    property alias defaultButtonText: _defaultButton.text

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

            Layout.column: 0
            Layout.row: 0
            Layout.preferredWidth: leftPadding + rightPadding + _base.valueTextMetrics.width

            validator: _base.amount.valueHumanValidator
            placeholderText: qsTr("Amount")

            Binding on text {
                restoreMode: Binding.RestoreNone
                when: !_valueField.focus && _base.amount.validStatus === BCommon.ValidStatus.Accept
                value: _base.amount.valueHuman
            }

            onTextEdited: {
                if (focus) {
                    _base.amount.setValueHuman(text)
                    _fiatValueField.focus = false // paranoid
                }
            }
            onTextChanged: {
                _base.amount.setValueHuman(text)
            }
        }
        BLabel {
            Layout.column: 1
            Layout.row: 0

            color: _base.color
            text: _base.amount.unit
        }

        Loader {
            active: _base.orientation !== Qt.Vertical
            sourceComponent: BLabel {
                Layout.column: 2
                Layout.row: 0
                font.bold: true
                color: _base.color
                text: "/"
            }
        }

        BTextField {
            id: _fiatValueField

            Layout.column: _base.orientation === Qt.Vertical ? 0 : 3
            Layout.row: _base.orientation === Qt.Vertical ? 1 : 0
            Layout.preferredWidth: leftPadding + rightPadding + _base.valueTextMetrics.width

            validator: _base.amount.fiatValueHumanValidator
            placeholderText: qsTr("Fiat amount")

            Binding on text {
                restoreMode: Binding.RestoreNone
                when: !_fiatValueField.focus && _base.amount.validStatus === BCommon.ValidStatus.Accept
                value: _base.amount.fiatValueHuman
            }

            onTextEdited: {
                if (focus) {
                    _base.amount.setFiatValueHuman(text)
                    _valueField.focus = false // paranoid
                }
            }
            onTextChanged: {
                _base.amount.setFiatValueHuman(text)
            }

        }
        BLabel {
            Layout.column: _base.orientation === Qt.Vertical ? 1 : 4
            Layout.row: _base.orientation === Qt.Vertical ? 1 : 0

            color: _base.color
            text: _base.amount.fiatUnit
        }

        Loader {
            active: _base.orientation !== Qt.Vertical
            sourceComponent: BLabel {
                Layout.column: 5
                Layout.row: 0

                font.bold: true
                color: _base.color
                text: "/"
            }
        }

        BButton {
            id: _defaultButton
            Layout.column: _base.orientation === Qt.Vertical ? 2 : 6
            Layout.row: 0
            Layout.rowSpan: _base.orientation === Qt.Vertical ? 2 : 1

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

    function clear() {
        _fiatValueField.clear()
        _valueField.clear()
    }
}
