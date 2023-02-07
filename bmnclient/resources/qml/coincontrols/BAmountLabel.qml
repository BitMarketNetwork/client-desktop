import QtQuick
import QtQuick.Controls.Material
import "../basiccontrols"

BControl {
    id: _base
    property var amount // AmountModel
    property color color: enabled ? Material.foreground : Material.hintTextColor
    property int orientation: Qt.Vertical

    contentItem: BGridLayout {
        columns: _base.orientation === Qt.Vertical ? 2 : 5

        BLabel {
            BLayout.alignment: Qt.AlignVCenter | Qt.AlignRight
            font.bold: true
            color: _base.color
            text: _base.amount.valueHuman
        }
        BLabel {
            BLayout.alignment: Qt.AlignVCenter | Qt.AlignLeft
            color: _base.color
            text: _base.amount.unit
        }

        Loader {
            active: _base.orientation !== Qt.Vertical
            visible: _base.orientation !== Qt.Vertical
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
            text: _base.amount.fiatValueHuman
        }
        BLabel {
            BLayout.alignment: Qt.AlignVCenter | Qt.AlignLeft
            color: _base.color
            text: _base.amount.fiatUnit
        }
    }
}
