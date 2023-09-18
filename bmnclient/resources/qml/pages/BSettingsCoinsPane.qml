import QtQuick
import QtQuick.Layouts

import "../basiccontrols"
import "../dialogcontrols"

BPane {
    id: _base
    property string title: qsTr("Coins")
    property string iconPath: _applicationManager.imagePath("icon-coins.svg")

    contentItem: BDialogScrollableLayout {
        BDialogPromptLabel {
            Layout.columnSpan: parent.columns
            text: qsTr("Uncheck unnecessary coins:")
        }
        Repeater {
            model: BBackend.coinList
            delegate: BDialogPromptLabel {
                Layout.column: 0
                Layout.row: index + 1
                text: modelObject.fullName
            }
        }
        Repeater {
            model: BBackend.coinList
            delegate: BDialogInputSwitch {
                Layout.column: 1
                Layout.row: index + 1
                checked: modelObject.state.isEnabled
                onCheckedChanged: {
                    modelObject.state.isEnabled = checked
                }
            }
        }
    }
}
