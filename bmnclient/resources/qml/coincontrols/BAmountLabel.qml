// JOK++
import QtQuick 2.15
import QtQuick.Controls.Material 2.15
import "../application"
import "../basiccontrols"

BControl {
    id: _base
    property var amount // AbstractAmountModel
    property color color: enabled ? Material.foreground : Material.hintTextColor
    property int orientation: Qt.Vertical

    contentItem: BGridLayout {
        columns: _base.orientation === Qt.Vertical ? 2 : 5

        BLabel {
            BLayout.alignment: Qt.AlignVCenter | Qt.AlignRight
            font.bold: true
            color: _base.color
            text: _base.amount ? _base.amount.valueHuman : BStandardText.template.amount
        }
        BLabel {
            BLayout.alignment: Qt.AlignVCenter | Qt.AlignLeft
            color: _base.color
            text: _base.amount ? _base.amount.unit : BStandardText.template.unit
        }

        Loader {
            active: _base.orientation !== Qt.Vertical
            sourceComponent: BLabel {
                font.bold: true
                color: _base.color
                text: "/"
            }
        }

        BLabel {
            BLayout.alignment: Qt.AlignVCenter | Qt.AlignRight
            font.bold: true
            color: _base.color
            text: _base.amount ? _base.amount.fiatValueHuman : BStandardText.template.amount
        }
        BLabel {
            BLayout.alignment: Qt.AlignVCenter | Qt.AlignLeft
            color: _base.color
            text: _base.amount ? _base.amount.fiatUnit : BStandardText.template.unit
        }
    }
}
