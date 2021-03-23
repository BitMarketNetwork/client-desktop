pragma Singleton

import QtQuick 2.15
import QtQuick.Controls.Material 2.15

QtObject {
    id: _base

    enum ValidStatus { // SYNC models.ValidStatus
        Unset,
        Reject,
        Accept
    }

    readonly property QtObject button: QtObject {
        readonly property string contextMenuRole: "⋮"
        readonly property string unfoldControlRole: "+" // TODO bad
        readonly property string foldControlRole: "−" // TODO bad

        readonly property string okRole: qsTr("OK")
        readonly property string createRole: qsTr("Create")
        readonly property string addRole: qsTr("Add")
        readonly property string continueRole: qsTr("Continue")
        readonly property string refreshRole: qsTr("Refresh")

        readonly property string yesRole: qsTr("Yes")
        readonly property string noRole: qsTr("No")

        readonly property string resetRole: qsTr("Reset")
        readonly property string cancelRole: qsTr("Cancel")
        readonly property string closeRole: qsTr("Close")

        readonly property string acceptRole: qsTr("Accept")
        readonly property string declineRole: qsTr("Decline")
    }

    readonly property QtObject symbol: QtObject {
        readonly property string acceptRole: "✔"
        readonly property int acceptRoleMaterialColor: Material.Green
        readonly property string rejectRole: "✘"
        readonly property int rejectRoleMaterialColor: Material.Red
    }

    readonly property QtObject amountTemplate: QtObject {
        readonly property int value: 0
        readonly property string valueHuman: "0.00"
        readonly property string unit: "XXX"
        readonly property string fiatValueHuman: "0.00"
        readonly property string fiatUnit: "YYY"
    }

    readonly property QtObject coinItemTemplate: QtObject {
        // TODO
    }

    readonly property QtObject addressItemTemplate: QtObject {
        readonly property string name: "unknown_address"
        readonly property QtObject amount: _base.amountTemplate
        readonly property QtObject state: QtObject {
            readonly property string label: ""
            readonly property bool watchOnly: false
            readonly property bool isUpdating: false
        }
        readonly property var txList: [] // TODO ListModel
    }

    readonly property QtObject txItemTemplate: QtObject {
        readonly property string name: "0000000000000000000000000000000000000000000000000000000000000000"
        readonly property QtObject amount: _base.amountTemplate
        readonly property QtObject feeAmount: _base.amountTemplate
        readonly property QtObject state: QtObject {
            readonly property int status: 0
            readonly property string timeHuman: "01/01/1970 00:00:00 UTC"
            readonly property int height: 0
            readonly property string heightHuman: "0"
            readonly property int confirmations: 0
            readonly property string confirmationsHuman: "0"
        }
        readonly property var inputList: [] // TODO ListModel
        readonly property var outputList: [] // TODO ListModel
    }

    readonly property variant txStatusMap: [
        [ qsTr("Pending"),   Material.Pink   ],
        [ qsTr("Confirmed"), Material.Yellow ],
        [ qsTr("Complete") , Material.Green  ]
    ]
}
