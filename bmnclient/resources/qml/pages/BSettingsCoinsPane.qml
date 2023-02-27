import QtQuick
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
                text: modelObject.fullName
            }
        }
        Repeater {
            model: BBackend.coinList
            delegate: BDialogInputSwitch {
                BLayout.column: 1
                BLayout.row: index + 1
                checked: modelObject.state.isEnabled
                onCheckedChanged: {
                    modelObject.state.isEnabled = checked
                }
            }
        }
    }
}
