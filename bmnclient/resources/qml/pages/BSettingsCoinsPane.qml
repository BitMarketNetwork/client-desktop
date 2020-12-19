import QtQuick 2.15
import "../basiccontrols"

BPane {
    id: _base
    property string title: qsTr("Coins")
    property string iconSource: _applicationManager.imageSource("icon-coins.svg")
    property variant coinListModel: null

    contentItem: BDialogScrollableLayout {
        BDialogPromtLabel {
            BLayout.columnSpan: parent.columns
            text: qsTr("Uncheck unnecessary coins:")
        }
        Repeater {
            model: _base.coinListModel
            delegate: BDialogPromtLabel {
                BLayout.column: 0
                BLayout.row: index + 1
                enabled: modelData.enabled
                text: modelData.fullName
            }
        }
        Repeater {
            model: _base.coinListModel
            delegate: BDialogInputSwitch {
                BLayout.column: 1
                BLayout.row: index + 1
                checked: modelData.visible
                enabled: modelData.enabled
                onCheckedChanged: {
                    modelData.visible = checked
                }
            }
        }
    }
}
