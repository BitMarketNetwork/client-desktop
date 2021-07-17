import QtQuick 2.15
import "../basiccontrols"

BPane {
    id: _base
    property string title: qsTr("Coins")
    property string iconPath: _applicationManager.imagePath("icon-coins.svg")

    contentItem: BDialogScrollableLayout {
        BDialogPromptLabel {
            BLayout.columnSpan: parent.columns
            text: qsTr("Uncheck unnecessary coins:")
        }
        Repeater {
            model: BBackend.coinList
            delegate: BDialogPromptLabel {
                BLayout.column: 0
                BLayout.row: index + 1
                text: model.fullName
            }
        }
        Repeater {
            model: BBackend.coinList
            delegate: BDialogInputSwitch {
                BLayout.column: 1
                BLayout.row: index + 1
                checked: model.state.isEnabled
                onCheckedChanged: {
                    model.state.isEnabled = checked
                }
            }
        }
    }
}
