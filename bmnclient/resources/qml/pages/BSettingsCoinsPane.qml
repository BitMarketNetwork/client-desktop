import QtQuick
import QtQuick.Layouts

import "../basiccontrols"

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
                text: model.fullName
            }
        }
        Repeater {
            model: BBackend.coinList
            delegate: BDialogInputSwitch {
                Layout.column: 1
                Layout.row: index + 1
                checked: model.state.isEnabled
                onCheckedChanged: {
                    model.state.isEnabled = checked
                }
            }
        }
    }
}
