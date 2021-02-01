pragma Singleton

import QtQuick 2.15
import QtQuick.Controls.Material 2.15

QtObject {
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

    readonly property QtObject template: QtObject {
        readonly property string amount: "0.00"
        readonly property string unit: "XXX"
    }

    readonly property variant txStatusMap: [
        [ qsTr("Pending"),     Material.Pink       ],
        [ qsTr("Unconfirmed"), Material.DeepOrange ],
        [ qsTr("Confirmed"),   Material.Indigo     ],
        [ qsTr("Complete") ,   Material.Green      ]
    ]
}
