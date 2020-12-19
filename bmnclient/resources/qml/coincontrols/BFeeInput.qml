import QtQuick 2.15
import "../basiccontrols"

BControl {
    id: _base

    property alias feeFactor: _slider.value
    property alias feeAmount: _amount.text
    property int confirmTime: 0

    contentItem: BGridLayout {
        columns: 2

        BTextField {
            id: _amount

            maximumLength: 40
            horizontalAlignment: TextInput.AlignLeft
            verticalAlignment: TextInput.AlignVCenter
            inputMethodHints: Qt.ImhFormattedNumbersOnly

            validator: RegExpValidator {
                regExp: /([0-9]+\.)?[0-9]+/
            }
            onTextEdited: {
                if (acceptableInput) {
                    //_fee.input(amount)
                    //_tx_controller.spbAmount = value
                }
            }
        }

        BLabel {
            id: _unit
            text: qsTr("satoshi/byte") // TODO dynamic
        }

        BSlider {
            id: _slider
            BLayout.columnSpan: parent.columns
            BLayout.minimumWidth: implicitWidth
            BLayout.fillWidth: true
        }

        BLabel {
            id: _target
            BLayout.columnSpan: parent.columns
            BLayout.minimumWidth: implicitWidth
            text: _base.esteem()
        }
    }

    function esteem() {
        var result = null
        const LIMIT = 5
        if (confirmTime < 0) {
            return qsTr("Transaction will be never confirmed")
        }

        if (confirmTime < LIMIT) {
            result = qsTr("immediately")
        } else if (confirmTime < 120) {
            result = qsTr("in %1 minutes").arg(LIMIT * (confirmTime / LIMIT).toFixed())
        } else {
            result = qsTr("in %1 hours").arg((confirmTime / 60).toFixed())
        }
        return qsTr("Transaction will be confirmed %1").arg(result)
    }
}
