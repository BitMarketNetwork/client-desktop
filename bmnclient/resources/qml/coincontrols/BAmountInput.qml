import QtQuick 2.15
import QtQuick.Controls.Material 2.15
import "../basiccontrols"

BControl {
    id: _base
    property BAmountObject amount: BAmountObject {}
    property alias value: _valueField.text
    property alias fiatValue: _fiatValueField.text
    property color color: _base.enabled ? _base.Material.foreground : _base.Material.hintTextColor
    property int orientation: Qt.Vertical

    property RegularExpressionValidator valueValidator: RegularExpressionValidator {
        regularExpression: /^\d{1,12}(?:[.]\d{0,8}|$)$/ // TODO dynamic, allow start with dot
    }
    property RegularExpressionValidator fiatValueValidator: RegularExpressionValidator {
        regularExpression: /^^\d{1,12}(?:[.]\d{0,2}|$)$$/ // TODO dynamic, allow start with dot
    }
    property TextMetrics valueTextMetrics: TextMetrics {
        text: "_888888888888.88888888_" // TODO dynamic
        font: _valueField.font
    }

    signal setMaxValue
    signal valueEdited
    signal fiatValueEdited

    contentItem: BGridLayout {
        columns: _base.orientation === Qt.Vertical ? 3 : 7
        columnSpacing: _valueField.rightPadding
        rowSpacing: _valueField.bottomPadding

        BTextField {
            id: _valueField

            BLayout.column: 0
            BLayout.row: 0
            BLayout.minimumWidth: BLayout.preferredWidth
            BLayout.preferredWidth: leftPadding + rightPadding + _base.valueTextMetrics.width

            inputMethodHints: Qt.ImhFormattedNumbersOnly
            validator: valueValidator
            horizontalAlignment: BTextField.AlignRight

            placeholderText: qsTr("Amount")
            text: amount.valueHuman

            onTextEdited: {
                processTextEdited(_valueField, _base.valueEdited)
            }
        }
        BLabel {
            BLayout.column: 1
            BLayout.row: 0

            color: _base.color
            text: amount.unit
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
            BLayout.minimumWidth: BLayout.preferredWidth
            BLayout.preferredWidth: leftPadding + rightPadding + _base.valueTextMetrics.width

            inputMethodHints: Qt.ImhFormattedNumbersOnly
            validator: fiatValueValidator
            horizontalAlignment: BTextField.AlignRight

            placeholderText: qsTr("Fiat amount")
            text: amount.fiatValueHuman
            readOnly: true // TODO no api support

            onTextEdited: {
                processTextEdited(_fiatValueField, _base.fiatValueEdited)
            }
        }
        BLabel {
            BLayout.column: _base.orientation === Qt.Vertical ? 1 : 4
            BLayout.row: _base.orientation === Qt.Vertical ? 1 : 0

            color: _base.color
            text: amount.fiatUnit
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
                _base.setMaxValue()
            }
        }
    }

    function processTextEdited(field, callback) {
        if (field.text.length === 0) {
            field.text = "0"
            field.selectAll()
            callback()
        }
        else if (field.acceptableInput) {
            callback()
        }
    }
}
