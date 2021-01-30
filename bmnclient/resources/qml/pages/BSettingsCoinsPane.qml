import QtQuick 2.15
import "../basiccontrols"

BPane {
    id: _base
    property string title: qsTr("Coins")
    property string iconPath: _applicationManager.imagePath("icon-coins.svg")

    contentItem: BDialogScrollableLayout {
        BDialogPromtLabel {
            BLayout.columnSpan: parent.columns
            text: qsTr("Uncheck unnecessary coins:")
        }
        Repeater {
            model: BBackend.coinManager.coinListModel
            delegate: BDialogPromtLabel {
                BLayout.column: 0
                BLayout.row: index + 1
                text: model.fullName
            }
        }
        Repeater {
            model: BBackend.coinManager.coinListModel
            delegate: BDialogInputSwitch {
                BLayout.column: 1
                BLayout.row: index + 1
                checked: model.state.visible
                onCheckedChanged: {
                    model.state.visible = checked
                }
            }
        }
    }
}
