import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../widgets"

Base {
    id: _base

    property alias amount: _amount.text
    property alias unit: _unit.text
    property alias color : _amount.color
    property int fontSize: 16
    property alias amounFontSize: _amount.font.pixelSize
    property int horAlignment: 0
    height: _amount.font.pixelSize

    antialiasing: true
    state: "default"

        SmallLabel{
            anchors{
                left: parent.left
                // leftMargin: 10
                /*
                right: parent.horizontalCenter
                rightMargin: 5
                */
                verticalCenter: parent.verticalCenter
            }
            id: _amount
            font.pixelSize: fontSize
            //verticalAlignment: Qt.AlignBottom
        }
        SmallLabel{
            anchors{
                // right: parent.right
                left: _amount.right
                leftMargin: 10
                /*
                leftMargin: 5
                */
                verticalCenter: parent.verticalCenter
            }
            id: _unit
            color: _amount.color
            font{
                pixelSize: fontSize
            }
            width: _unit_fmetric.averageCharacterWidth * _unit.text.length
        }
        FontMetrics{
            id: _unit_fmetric
            font: _unit.font
        }

        states: [
            State {
                name: "default"
                when: _unit.text === ""
                AnchorChanges{
                    target: _unit
                    anchors{
                        horizontalCenter: parent.horizontalCenter
                    }
                }
            },
            State {
                name: "right"
                AnchorChanges{
                    target: _unit
                    anchors{
                        right: parent.right
                    }
                }
                PropertyChanges {
                    target: _unit
                    horizontalAlignment: Text.AlignRight
                }
                PropertyChanges {
                    target: _amount
                    horizontalAlignment: Text.AlignRight
                }
            }
        ]
}
