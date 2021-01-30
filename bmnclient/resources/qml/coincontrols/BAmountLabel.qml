import QtQuick 2.15
import QtQuick.Controls.Material 2.15
import "../basiccontrols"

BControl {
    id: _base
    property var amount // AmountModel
    property color color: _base.enabled ? _base.Material.foreground : _base.Material.hintTextColor
    property int orientation: Qt.Vertical

    contentItem: BGridLayout {
        columns: _base.orientation === Qt.Vertical ? 2 : 5

        BLabel {
            BLayout.alignment: Qt.AlignVCenter | Qt.AlignRight
            font.bold: true
            color: _base.color
            text: amount.valueHuman
        }
        BLabel {
            BLayout.alignment: Qt.AlignVCenter | Qt.AlignLeft
            color: _base.color
            text: amount.unit
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
            text: amount.fiatValueHuman
        }
        BLabel {
            BLayout.alignment: Qt.AlignVCenter | Qt.AlignLeft
            color: _base.color
            text: amount.fiatUnit
        }
    }
}
